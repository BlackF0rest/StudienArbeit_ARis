from __future__ import annotations

from copy import deepcopy
from typing import Any

from repositories.sqlite_repo import SQLiteRepository


DEFAULT_DEVICE_SETTINGS: dict[str, Any] = {
    "brightness": 75,
    "volume": 50,
    "language": "de-DE",
    "flags": {
        "companion_diagnostics": True,
        "teleprompter_preview": True,
    },
    "runtime_flags": {
        "companion_diagnostics": True,
        "teleprompter_preview": True,
    },
}


class DeviceSettingsService:
    def __init__(self, repo: SQLiteRepository):
        self._repo = repo

    def get_settings(self) -> dict[str, Any]:
        stored = self._repo.get_device_settings()
        if stored is None:
            defaults = deepcopy(DEFAULT_DEVICE_SETTINGS)
            self._repo.save_device_settings(defaults)
            return defaults

        merged = deepcopy(DEFAULT_DEVICE_SETTINGS)
        merged.update(stored)

        for nested_key in ("flags", "runtime_flags"):
            existing = merged.get(nested_key)
            if not isinstance(existing, dict):
                merged[nested_key] = deepcopy(DEFAULT_DEVICE_SETTINGS[nested_key])

        return merged

    def update_settings(self, patch: dict[str, Any]) -> dict[str, Any]:
        current = self.get_settings()

        for key in ("brightness", "volume", "language"):
            if key in patch:
                current[key] = patch[key]

        normalized_flags = self._normalize_flags(patch.get("flags"))
        normalized_runtime_flags = self._normalize_flags(patch.get("runtime_flags"))

        if normalized_flags is not None:
            current["flags"] = normalized_flags
            current["runtime_flags"] = normalized_flags

        if normalized_runtime_flags is not None:
            current["runtime_flags"] = normalized_runtime_flags
            if normalized_flags is None:
                current["flags"] = normalized_runtime_flags

        self._repo.save_device_settings(current)
        return current

    @staticmethod
    def _normalize_flags(value: Any) -> dict[str, bool] | None:
        if value is None:
            return None

        if not isinstance(value, dict):
            return {}

        return {
            str(name): bool(flag)
            for name, flag in value.items()
            if isinstance(flag, bool)
        }
