from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config_loader import ConfigLoader, RuntimeConfig
from .event_bus import SharedEventBus
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
        self.registry.register(
            ModuleLifecycleManager(name="communication-adapter", version="0.1.0"),
            ModuleCategory.COMMUNICATION_ADAPTER,
        )

    def start_all(self) -> None:
        for module in self.registry.modules.values():
            module.start()

    def stop_all(self) -> None:
        for module in self.registry.modules.values():
            module.stop()
