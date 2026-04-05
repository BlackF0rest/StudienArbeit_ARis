from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .comm import (
    BluetoothAdapter,
    ConnectionManager,
    ConnectionState,
    TransportTranslator,
    USBDebugAdapter,
    WiFiAdapter,
)
from .config_loader import ConfigLoader, RuntimeConfig
from .event_bus import SharedEventBus
from .hardware.subscriptions import (
    BasicHUDSubscription,
    NavigationSubscription,
    TeleprompterSubscription,
)
from .module_lifecycle import ModuleLifecycleManager, ModuleMetadata
from .module_registry import CentralModuleRegistry, ModuleCategory
from .pc_interface import PCInterfaceOrchestrator
from .startup_profiles import resolve_profile


@dataclass
class OnboardRuntime:
    config_loader: ConfigLoader
    registry: CentralModuleRegistry
    event_bus: SharedEventBus
    telemetry_log: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_config(cls, config_path: str | Path) -> "OnboardRuntime":
        return cls(
            config_loader=ConfigLoader(config_path),
            registry=CentralModuleRegistry(),
            event_bus=SharedEventBus(),
        )

    def _telemetry_hook(self, module_name: str):
        def emit(event_type: str, payload: dict[str, Any]) -> None:
            self.telemetry_log.append(
                {
                    "module": module_name,
                    "event_type": event_type,
                    "payload": payload,
                }
            )
            self.telemetry_log[:] = self.telemetry_log[-100:]

        return emit

    def load_config(self) -> RuntimeConfig:
        config = self.config_loader.load()
        profile = resolve_profile(config.profile)

        config.log_level = profile.log_level
        config.ui_enabled = profile.ui_enabled
        config.stable_defaults = profile.stable_defaults
        return config

    def register_core_modules(self) -> None:
        self.registry.register(
            ModuleLifecycleManager(
                name="backend-service",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="Backend service entrypoint",
                    permissions=("network.read", "network.write"),
                ),
                custom_health_check=lambda: {"service_ready": True},
                telemetry_hook=self._telemetry_hook("backend-service"),
            ),
            ModuleCategory.BACKEND_SERVICE,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="feature-app-host",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="Feature application host runtime",
                    permissions=("clock.read", "storage.read", "storage.write"),
                    dependencies=("backend-service",),
                ),
                custom_health_check=lambda: {"modules": len(self.registry.modules)},
                telemetry_hook=self._telemetry_hook("feature-app-host"),
            ),
            ModuleCategory.FEATURE_APP_HOST,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="hardware-adapter",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="Hardware sensor/IO adapter",
                    permissions=("sensors.read",),
                    dependencies=("feature-app-host",),
                ),
                custom_health_check=lambda: {"event_bus": "ready"},
                telemetry_hook=self._telemetry_hook("hardware-adapter"),
            ),
            ModuleCategory.HARDWARE_ADAPTER,
        )
        self.register_communication_modules()

    def register_communication_modules(self) -> dict[str, object]:
        connection_manager = ConnectionManager(self.event_bus)
        translator = TransportTranslator()
        bluetooth = BluetoothAdapter(connection_manager=connection_manager)
        usb_debug = USBDebugAdapter(connection_manager=connection_manager)
        wifi = WiFiAdapter(connection_manager=connection_manager)
        pc_interface = PCInterfaceOrchestrator(connection_manager=connection_manager)
        usb_debug.register_panel_provider("pc_link", pc_interface.diagnostic_panel)

        modules = {
            "connection_manager": connection_manager,
            "translator": translator,
            "bluetooth": bluetooth,
            "usb_debug": usb_debug,
            "wifi": wifi,
            "pc_interface": pc_interface,
        }

        self.registry.register(
            ModuleLifecycleManager(
                name="connection-manager",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="Connection state orchestrator",
                    permissions=("network.read", "network.write"),
                    dependencies=("backend-service",),
                ),
                on_start=lambda: connection_manager.set_state(
                    "runtime", ConnectionState.CONNECTED, reason="connection manager active"
                ),
                on_stop=lambda: connection_manager.set_state(
                    "runtime", ConnectionState.DISCONNECTED, reason="connection manager stopped"
                ),
                custom_health_check=lambda: connection_manager.health(),
                telemetry_hook=self._telemetry_hook("connection-manager"),
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="bluetooth-adapter",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="Bluetooth adapter",
                    permissions=("network.read", "network.write"),
                    dependencies=("connection-manager",),
                ),
                on_stop=bluetooth.disconnect_peer,
                custom_health_check=lambda: bluetooth.health(),
                telemetry_hook=self._telemetry_hook("bluetooth-adapter"),
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="usb-debug-adapter",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="USB diagnostics and command channel",
                    permissions=("network.read", "network.write"),
                    dependencies=("connection-manager",),
                ),
                on_start=usb_debug.attach,
                on_stop=usb_debug.detach,
                custom_health_check=lambda: usb_debug.health(),
                telemetry_hook=self._telemetry_hook("usb-debug-adapter"),
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="pc-interface",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="PC link session manager + pixel streaming orchestrator",
                    permissions=("network.read", "network.write", "display.write"),
                    dependencies=("connection-manager",),
                ),
                custom_health_check=lambda: pc_interface.health(),
                telemetry_hook=self._telemetry_hook("pc-interface"),
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )

        self.registry.register(
            ModuleLifecycleManager(
                name="wifi-adapter",
                version="0.1.0",
                metadata=ModuleMetadata(
                    description="WiFi client interface",
                    permissions=("network.read", "network.write"),
                    dependencies=("connection-manager",),
                ),
                on_start=wifi.connect,
                on_stop=wifi.disconnect,
                custom_health_check=lambda: wifi.health(),
                telemetry_hook=self._telemetry_hook("wifi-adapter"),
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )

        return modules

    def register_feature_subscriptions(self) -> dict[str, object]:
        subscriptions = {
            "basic_hud": BasicHUDSubscription(self.event_bus),
            "navigation": NavigationSubscription(self.event_bus),
            "teleprompter": TeleprompterSubscription(self.event_bus),
        }
        for subscription in subscriptions.values():
            subscription.attach()
        return subscriptions

    def start_all(self) -> None:
        for module in self.registry.modules.values():
            module.start()

    def stop_all(self) -> None:
        for module in self.registry.modules.values():
            module.stop()
