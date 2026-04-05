from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

from .connection_manager import ConnectionManager, ConnectionState
from .translator import TransportPayload


class USBDebugAdapter:
    """USB command channel + diagnostics endpoint for development tooling."""

    def __init__(self, connection_manager: ConnectionManager, adapter_name: str = "usb") -> None:
        self._connection_manager = connection_manager
        self._adapter_name = adapter_name
        self._command_queue: deque[TransportPayload] = deque()
        self._diagnostics: deque[dict[str, Any]] = deque(maxlen=200)
        self._listeners: list[Callable[[TransportPayload], None]] = []
        self._attached = False

    def attach(self) -> None:
        self._attached = True
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.CONNECTED,
            reason="usb command channel attached",
        )

    def detach(self) -> None:
        self._attached = False
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.DISCONNECTED,
            reason="usb command channel detached",
        )

    def on_payload(self, callback: Callable[[TransportPayload], None]) -> None:
        self._listeners.append(callback)

    def receive_command(self, payload: TransportPayload) -> None:
        self._command_queue.append(payload)
        for listener in list(self._listeners):
            listener(payload)

    def next_command(self) -> TransportPayload | None:
        return self._command_queue.popleft() if self._command_queue else None

    def publish_diagnostic(self, component: str, status: str, details: dict[str, Any] | None = None) -> None:
        self._diagnostics.append(
            {
                "component": component,
                "status": status,
                "details": details or {},
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    def diagnostics_endpoint(self, limit: int = 50) -> dict[str, Any]:
        data = list(self._diagnostics)[-limit:]
        return {
            "adapter": self._adapter_name,
            "connected": self._attached,
            "pending_commands": len(self._command_queue),
            "diagnostics": data,
        }

    def health(self) -> dict[str, Any]:
        return {
            "adapter": self._adapter_name,
            "connected": self._attached,
            "queued_commands": len(self._command_queue),
            "diagnostic_entries": len(self._diagnostics),
        }
