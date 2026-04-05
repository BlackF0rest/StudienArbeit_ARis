from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class StreamQuality(str, Enum):
    ULTRA = "ultra"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PixelStreamingState:
    connected: bool = False
    reconnect_attempts: int = 0
    quality: StreamQuality = StreamQuality.HIGH
    last_event_at: str = datetime.now(tz=timezone.utc).isoformat()


class PixelStreamingOrchestrator:
    """Coordinates Pixel Streaming connect/reconnect and quality fallback."""

    _QUALITY_STEPS = [
        StreamQuality.ULTRA,
        StreamQuality.HIGH,
        StreamQuality.MEDIUM,
        StreamQuality.LOW,
    ]

    def __init__(self) -> None:
        self._state = PixelStreamingState()

    def connect(self) -> None:
        self._state.connected = True
        self._state.reconnect_attempts = 0
        self._mark_event()

    def disconnect(self) -> None:
        self._state.connected = False
        self._mark_event()

    def reconnect(self) -> None:
        self._state.reconnect_attempts += 1
        self._state.connected = True
        self._mark_event()

    def fallback_quality(self) -> StreamQuality:
        current_index = self._QUALITY_STEPS.index(self._state.quality)
        next_index = min(current_index + 1, len(self._QUALITY_STEPS) - 1)
        self._state.quality = self._QUALITY_STEPS[next_index]
        self._mark_event()
        return self._state.quality

    def set_quality(self, quality: StreamQuality) -> None:
        self._state.quality = quality
        self._mark_event()

    def snapshot(self) -> dict[str, Any]:
        return {
            "connected": self._state.connected,
            "reconnect_attempts": self._state.reconnect_attempts,
            "quality": self._state.quality.value,
            "last_event_at": self._state.last_event_at,
        }

    def _mark_event(self) -> None:
        self._state.last_event_at = datetime.now(tz=timezone.utc).isoformat()
