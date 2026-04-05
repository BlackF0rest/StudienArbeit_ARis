from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..event_bus import RuntimeEvent, SharedEventBus


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass(frozen=True)
class ConnectionTransition:
    adapter: str
    previous: ConnectionState
    current: ConnectionState
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


class ConnectionManager:
    """Tracks transport states and publishes connection-status events."""

    def __init__(self, event_bus: SharedEventBus) -> None:
        self._event_bus = event_bus
        self._states: dict[str, ConnectionState] = {}
        self._history: list[ConnectionTransition] = []

    def set_state(self, adapter: str, state: ConnectionState, reason: str = "") -> None:
        previous = self._states.get(adapter, ConnectionState.DISCONNECTED)
        self._states[adapter] = state
        transition = ConnectionTransition(
            adapter=adapter,
            previous=previous,
            current=state,
            reason=reason,
        )
        self._history.append(transition)
        self._event_bus.publish(
            RuntimeEvent.CONNECTION_STATUS,
            {
                "adapter": adapter,
                "previous": previous.value,
                "state": state.value,
                "reason": reason,
                "timestamp": transition.timestamp,
            },
        )

    def status(self) -> dict[str, str]:
        return {adapter: state.value for adapter, state in self._states.items()}

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        recent = self._history[-limit:]
        return [
            {
                "adapter": item.adapter,
                "previous": item.previous.value,
                "state": item.current.value,
                "reason": item.reason,
                "timestamp": item.timestamp,
            }
            for item in recent
        ]
