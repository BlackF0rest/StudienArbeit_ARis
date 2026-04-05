from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .module_lifecycle import ModuleLifecycleManager


class ModuleCategory(str, Enum):
    BACKEND_SERVICE = "backend_service"
    FEATURE_APP_HOST = "feature_app_host"
    HARDWARE_ADAPTER = "hardware_adapter"
    COMMUNICATION_ADAPTER = "communication_adapter"


@dataclass
class CentralModuleRegistry:
    """Tracks all module instances and their category mappings."""

    modules: dict[str, ModuleLifecycleManager] = field(default_factory=dict)
    category_map: dict[ModuleCategory, list[str]] = field(
        default_factory=lambda: {category: [] for category in ModuleCategory}
    )

    def register(self, module: ModuleLifecycleManager, category: ModuleCategory) -> None:
        missing_dependencies = [
            dependency
            for dependency in module.metadata.dependencies
            if dependency and dependency not in self.modules
        ]
        if missing_dependencies:
            raise ValueError(
                f"Cannot register '{module.name}': missing dependencies {missing_dependencies}"
            )

        self.modules[module.name] = module
        if module.name not in self.category_map[category]:
            self.category_map[category].append(module.name)

    def unregister(self, module_name: str) -> None:
        self.modules.pop(module_name, None)
        for names in self.category_map.values():
            if module_name in names:
                names.remove(module_name)

    def get_module(self, module_name: str) -> ModuleLifecycleManager | None:
        return self.modules.get(module_name)

    def by_category(self, category: ModuleCategory) -> list[ModuleLifecycleManager]:
        return [
            self.modules[name]
            for name in self.category_map[category]
            if name in self.modules
        ]

    def all_health(self) -> dict[str, dict[str, str | None | dict]]:
        return {name: module.health() for name, module in self.modules.items()}
