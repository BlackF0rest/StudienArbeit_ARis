from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any

from .comm import BluetoothAdapter, ConnectionManager, USBDebugAdapter, WiFiAdapter
from .event_bus import EventMessage, RuntimeEvent, SharedEventBus
from .module_registry import CentralModuleRegistry


class DebugInterfaceModule:
    """Local diagnostics surface + protected debug API handlers."""

    def __init__(
        self,
        registry: CentralModuleRegistry,
        event_bus: SharedEventBus,
        connection_manager: ConnectionManager,
        bluetooth: BluetoothAdapter,
        usb_debug: USBDebugAdapter,
        wifi: WiFiAdapter,
        telemetry_log: list[dict[str, Any]],
        debug_token: str | None = None,
        sample_size: int = 120,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._connection_manager = connection_manager
        self._bluetooth = bluetooth
        self._usb_debug = usb_debug
        self._wifi = wifi
        self._telemetry_log = telemetry_log
        self._debug_token = debug_token
        self._sampled_events: deque[dict[str, Any]] = deque(maxlen=sample_size)
        self._sensor_signals: deque[dict[str, Any]] = deque(maxlen=sample_size)
        self._hid_signals: deque[dict[str, Any]] = deque(maxlen=sample_size)

        for event in RuntimeEvent:
            self._event_bus.subscribe(event, self._sample_event)

    def _sample_event(self, message: EventMessage) -> None:
        sampled = {
            "event": message.event.value,
            "payload": message.payload,
            "sampled_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._sampled_events.append(sampled)

        if message.event in (RuntimeEvent.SENSOR_UPDATE, RuntimeEvent.HARDWARE_EVENT):
            self._sensor_signals.append(sampled)

        payload_source = str(message.payload.get("source", ""))
        payload_event = str(message.payload.get("event_type", ""))
        if message.event is RuntimeEvent.BUTTON_PRESS or payload_source.startswith("hid:") or payload_event.startswith("input."):
            self._hid_signals.append(sampled)

    def module_health_dashboard(self) -> dict[str, Any]:
        module_health = self._registry.all_health()
        states = [health.get("status") for health in module_health.values()]
        running = sum(1 for state in states if state == "running")
        errors = sum(1 for state in states if state == "error")

        return {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "summary": {
                "modules_total": len(module_health),
                "running": running,
                "errors": errors,
            },
            "modules": module_health,
        }

    def event_bus_monitor(self, limit: int = 40) -> dict[str, Any]:
        events = list(self._sampled_events)[-limit:]
        counters: dict[str, int] = {}
        for item in events:
            counters[item["event"]] = counters.get(item["event"], 0) + 1
        return {
            "sample_window": limit,
            "sampled_events": events,
            "event_counts": counters,
        }

    def transport_status(self) -> dict[str, Any]:
        states = self._connection_manager.status()
        return {
            "bluetooth": {
                "state": states.get("bluetooth", "disconnected"),
                "health": self._bluetooth.health(),
            },
            "usb": {
                "state": states.get("usb", "disconnected"),
                "health": self._usb_debug.health(),
            },
            "wifi": {
                "state": states.get("wifi", "disconnected"),
                "health": self._wifi.health(),
            },
            "connection_history": self._connection_manager.history(limit=25),
        }

    def sensor_hid_signal_monitor(self, limit: int = 40) -> dict[str, Any]:
        return {
            "sensor": list(self._sensor_signals)[-limit:],
            "hid": list(self._hid_signals)[-limit:],
        }

    def export_logs(self, limit: int = 200) -> dict[str, Any]:
        return {
            "exported_at": datetime.now(tz=timezone.utc).isoformat(),
            "telemetry": self._telemetry_log[-limit:],
            "event_samples": list(self._sampled_events)[-limit:],
            "usb_diagnostics": self._usb_debug.diagnostics_endpoint(limit=limit),
        }

    def run_integration_smoke_check(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        for name, module in self._registry.modules.items():
            health = module.health()
            checks.append(
                {
                    "name": name,
                    "status": "pass" if health.get("status") in {"running", "initialized"} else "warn",
                    "module_state": health.get("status"),
                }
            )

        transport = self.transport_status()
        for adapter in ("bluetooth", "usb", "wifi"):
            checks.append(
                {
                    "name": f"transport:{adapter}",
                    "status": "pass" if transport[adapter]["state"] != "error" else "fail",
                    "module_state": transport[adapter]["state"],
                }
            )

        failed = [item for item in checks if item["status"] == "fail"]
        warned = [item for item in checks if item["status"] == "warn"]
        return {
            "ok": not failed,
            "failed": len(failed),
            "warnings": len(warned),
            "checks": checks,
            "completed_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    def execute_admin_command(self, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}

        if command == "restart_module":
            module_name = str(payload.get("module", "")).strip()
            module = self._registry.get_module(module_name)
            if not module:
                return {"ok": False, "error": f"unknown module '{module_name}'"}
            module.stop()
            module.start()
            return {"ok": True, "command": command, "module": module_name}

        if command == "clear_queue_cache":
            cleared = {
                "usb_commands": self._usb_debug.clear_command_queue(),
                "usb_diagnostics": self._usb_debug.clear_diagnostics(),
                "wifi_counters": self._wifi.clear_counters(),
                "event_samples": self._clear_samples(),
            }
            return {"ok": True, "command": command, "cleared": cleared}

        if command == "export_logs":
            return {"ok": True, "command": command, "logs": self.export_logs(limit=int(payload.get("limit", 200)))}

        if command == "run_integration_smoke_check":
            return {
                "ok": True,
                "command": command,
                "results": self.run_integration_smoke_check(),
            }

        return {"ok": False, "error": f"unsupported command '{command}'"}

    def _clear_samples(self) -> dict[str, int]:
        cleared = {
            "events": len(self._sampled_events),
            "sensor": len(self._sensor_signals),
            "hid": len(self._hid_signals),
        }
        self._sampled_events.clear()
        self._sensor_signals.clear()
        self._hid_signals.clear()
        return cleared

    def local_ui_snapshot(self) -> dict[str, Any]:
        return {
            "dashboard": self.module_health_dashboard(),
            "event_bus": self.event_bus_monitor(limit=30),
            "transports": self.transport_status(),
            "signals": self.sensor_hid_signal_monitor(limit=30),
            "admin_commands": [
                "restart_module",
                "clear_queue_cache",
                "export_logs",
                "run_integration_smoke_check",
            ],
        }

    def protected_debug_api(
        self, command: str, payload: dict[str, Any] | None = None, token: str | None = None
    ) -> dict[str, Any]:
        if self._debug_token and token != self._debug_token:
            return {"ok": False, "error": "unauthorized"}

        if command == "dashboard":
            return {"ok": True, "data": self.local_ui_snapshot()}

        if command == "event_bus_monitor":
            limit = int((payload or {}).get("limit", 40))
            return {"ok": True, "data": self.event_bus_monitor(limit=limit)}

        if command == "transport_status":
            return {"ok": True, "data": self.transport_status()}

        if command == "sensor_hid_signal_monitor":
            limit = int((payload or {}).get("limit", 40))
            return {"ok": True, "data": self.sensor_hid_signal_monitor(limit=limit)}

        return self.execute_admin_command(command, payload=payload)

    def health(self) -> dict[str, Any]:
        return {
            "sampled_events": len(self._sampled_events),
            "sensor_samples": len(self._sensor_signals),
            "hid_samples": len(self._hid_signals),
            "protected_api": bool(self._debug_token),
        }
