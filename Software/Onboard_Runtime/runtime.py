from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
from .module_lifecycle import ModuleLifecycleManager
from .module_registry import CentralModuleRegistry, ModuleCategory
from .startup_profiles import resolve_profile


@dataclass
class OnboardRuntime:
    config_loader: ConfigLoader
    registry: CentralModuleRegistry
    event_bus: SharedEventBus

    @classmethod
    def from_config(cls, config_path: str | Path) -> "OnboardRuntime":
        return cls(
            config_loader=ConfigLoader(config_path),
            registry=CentralModuleRegistry(),
            event_bus=SharedEventBus(),
        )

    def load_config(self) -> RuntimeConfig:
        config = self.config_loader.load()
        profile = resolve_profile(config.profile)

        config.log_level = profile.log_level
        config.ui_enabled = profile.ui_enabled
        config.stable_defaults = profile.stable_defaults
        return config

    def register_core_modules(self) -> None:
        self.registry.register(
            ModuleLifecycleManager(name="backend-service", version="0.1.0"),
            ModuleCategory.BACKEND_SERVICE,
        )
        self.registry.register(
            ModuleLifecycleManager(name="feature-app-host", version="0.1.0"),
            ModuleCategory.FEATURE_APP_HOST,
        )
        self.registry.register(
            ModuleLifecycleManager(name="hardware-adapter", version="0.1.0"),
            ModuleCategory.HARDWARE_ADAPTER,
        )
        self.register_communication_modules()

    def register_communication_modules(self) -> dict[str, object]:
        connection_manager = ConnectionManager(self.event_bus)
        translator = TransportTranslator()
        bluetooth = BluetoothAdapter(connection_manager=connection_manager)
        usb_debug = USBDebugAdapter(connection_manager=connection_manager)
        wifi = WiFiAdapter(connection_manager=connection_manager)

        modules = {
            "connection_manager": connection_manager,
            "translator": translator,
            "bluetooth": bluetooth,
            "usb_debug": usb_debug,
            "wifi": wifi,
        }

        self.registry.register(
            ModuleLifecycleManager(
                name="connection-manager",
                version="0.1.0",
                on_start=lambda: connection_manager.set_state(
                    "runtime", ConnectionState.CONNECTED, reason="connection manager active"
                ),
                on_stop=lambda: connection_manager.set_state(
                    "runtime", ConnectionState.DISCONNECTED, reason="connection manager stopped"
                ),
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="bluetooth-adapter",
                version="0.1.0",
                on_stop=bluetooth.disconnect_peer,
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="usb-debug-adapter",
                version="0.1.0",
                on_start=usb_debug.attach,
                on_stop=usb_debug.detach,
            ),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )
        self.registry.register(
            ModuleLifecycleManager(
                name="wifi-adapter",
                version="0.1.0",
                on_start=wifi.connect,
                on_stop=wifi.disconnect,
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
