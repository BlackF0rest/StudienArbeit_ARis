from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class ModuleState(str, Enum):
    STOPPED = "stopped"
    INITIALIZED = "initialized"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class ModuleMetadata:
    """Registration metadata required for feature module API."""

    description: str = ""
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()


@dataclass
class ModuleLifecycleManager:
    """Standard lifecycle contract for onboard modules."""

    name: str
    version: str
    metadata: ModuleMetadata = field(default_factory=ModuleMetadata)
    on_init: Optional[Callable[[], None]] = None
    on_start: Optional[Callable[[], None]] = None
    on_stop: Optional[Callable[[], None]] = None
    custom_health_check: Optional[Callable[[], dict[str, Any]]] = None
    telemetry_hook: Optional[Callable[[str, dict[str, Any]], None]] = None
    state: ModuleState = field(default=ModuleState.STOPPED, init=False)
    last_error: Optional[str] = field(default=None, init=False)
    started_at: Optional[datetime] = field(default=None, init=False)

    def _emit(self, event_type: str, payload: Optional[dict[str, Any]] = None) -> None:
        if self.telemetry_hook:
            self.telemetry_hook(event_type, payload or {})

    def init(self) -> None:
        try:
            if self.on_init:
                self.on_init()
            self.state = ModuleState.INITIALIZED
            self.last_error = None
            self._emit("module.init", {"state": self.state.value})
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.state = ModuleState.ERROR
            self.last_error = str(exc)
            self._emit("module.error", {"stage": "init", "error": self.last_error})
            raise

    def start(self) -> None:
        if self.state == ModuleState.STOPPED:
            self.init()
        try:
            if self.on_start:
                self.on_start()
            self.state = ModuleState.RUNNING
            self.last_error = None
            self.started_at = datetime.now(tz=timezone.utc)
            self._emit("module.start", {"state": self.state.value})
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.state = ModuleState.ERROR
            self.last_error = str(exc)
            self._emit("module.error", {"stage": "start", "error": self.last_error})
            raise

    def stop(self) -> None:
        try:
            if self.on_stop:
                self.on_stop()
            self.state = ModuleState.STOPPED
            self._emit("module.stop", {"state": self.state.value})
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.state = ModuleState.ERROR
            self.last_error = str(exc)
            self._emit("module.error", {"stage": "stop", "error": self.last_error})
            raise

    def health(self) -> dict[str, str | None | dict[str, Any]]:
        extra: dict[str, Any] = {}
        if self.custom_health_check:
            try:
                extra = self.custom_health_check()
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                extra = {"custom_health_error": str(exc)}

        return {
            "name": self.name,
            "status": self.state.value,
            "last_error": self.last_error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "metadata": {
                "description": self.metadata.description,
                "permissions": list(self.metadata.permissions),
                "dependencies": list(self.metadata.dependencies),
            },
            "checks": extra,
        }

    def get_version(self) -> str:
        return self.version
