from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RuntimeConfig:
    profile: str
    log_level: str
    ui_enabled: bool
    stable_defaults: bool
    settings: dict[str, Any]


class ConfigLoader:
    """Loads base configuration from JSON file and overlays environment variables."""

    ENV_PREFIX = "ARIS_RUNTIME_"

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)

    def load(self) -> RuntimeConfig:
        raw: dict[str, Any] = {}
        if self.config_path.exists():
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))

        env_overrides = self._collect_env_overrides()
        merged = {**raw, **env_overrides}

        return RuntimeConfig(
            profile=str(merged.get("profile", "demo")),
            log_level=str(merged.get("log_level", "INFO")),
            ui_enabled=self._to_bool(merged.get("ui_enabled", True)),
            stable_defaults=self._to_bool(merged.get("stable_defaults", True)),
            settings=merged,
        )

    def _collect_env_overrides(self) -> dict[str, Any]:
        overrides: dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                normalized_key = key.removeprefix(self.ENV_PREFIX).lower()
                overrides[normalized_key] = value
        return overrides

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
