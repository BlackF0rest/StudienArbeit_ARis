from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional


class ModuleState(str, Enum):
    STOPPED = "stopped"
    INITIALIZED = "initialized"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class ModuleLifecycleManager:
    """Standard lifecycle contract for onboard modules."""

    name: str
    version: str
    on_init: Optional[Callable[[], None]] = None
    on_start: Optional[Callable[[], None]] = None
    on_stop: Optional[Callable[[], None]] = None
    state: ModuleState = field(default=ModuleState.STOPPED, init=False)
    last_error: Optional[str] = field(default=None, init=False)
    started_at: Optional[datetime] = field(default=None, init=False)

    def init(self) -> None:
        try:
            if self.on_init:
                self.on_init()
            self.state = ModuleState.INITIALIZED
            self.last_error = None
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.state = ModuleState.ERROR
            self.last_error = str(exc)
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
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.state = ModuleState.ERROR
            self.last_error = str(exc)
            raise

    def stop(self) -> None:
        try:
            if self.on_stop:
                self.on_stop()
            self.state = ModuleState.STOPPED
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.state = ModuleState.ERROR
            self.last_error = str(exc)
            raise

    def health(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "status": self.state.value,
            "last_error": self.last_error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }

    def get_version(self) -> str:
        return self.version
