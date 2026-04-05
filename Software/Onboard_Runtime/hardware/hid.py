from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from .events import HardwareEvent


class PressSemantics(str, Enum):
    SHORT = "short_press"
    LONG = "long_press"


@dataclass
class _PressState:
    started_at: datetime


class HIDInputAdapter:
    """Processes raw button transitions into debounced short/long press events."""

    def __init__(
        self,
        debounce_window_ms: int = 50,
        long_press_threshold_ms: int = 600,
    ) -> None:
        self._debounce_window = timedelta(milliseconds=debounce_window_ms)
        self._long_press_threshold = timedelta(milliseconds=long_press_threshold_ms)
        self._active_presses: dict[str, _PressState] = {}
        self._last_transition: dict[str, datetime] = {}

    def ingest_transition(
        self,
        button_id: str,
        pressed: bool,
        at: datetime | None = None,
    ) -> HardwareEvent | None:
        timestamp = at or datetime.now(tz=timezone.utc)
        if self._is_debounced(button_id, timestamp):
            return None

        self._last_transition[button_id] = timestamp
        if pressed:
            self._active_presses[button_id] = _PressState(started_at=timestamp)
            return None

        active = self._active_presses.pop(button_id, None)
        if active is None:
            return None

        duration = timestamp - active.started_at
        press_type = (
            PressSemantics.LONG if duration >= self._long_press_threshold else PressSemantics.SHORT
        )

        control_value: str | float
        if press_type is PressSemantics.LONG:
            control_value = "toggle_pause_resume"
        else:
            control_value = "speed_up"

        return HardwareEvent(
            event_type="input.control",
            source=f"hid:{button_id}",
            value={
                "press": press_type.value,
                "duration_ms": round(duration.total_seconds() * 1000),
                "control": control_value,
            },
            unit=None,
            timestamp=timestamp,
        )

    def _is_debounced(self, button_id: str, timestamp: datetime) -> bool:
        previous = self._last_transition.get(button_id)
        if previous is None:
            return False
        return timestamp - previous < self._debounce_window
