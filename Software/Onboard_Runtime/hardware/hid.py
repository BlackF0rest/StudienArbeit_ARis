from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .events import HardwareEvent


@dataclass
class _PressState:
    started_at: datetime


@dataclass
class _TapState:
    tap_count: int
    first_tap_at: datetime
    last_tap_duration_ms: int


class HIDInputAdapter:
    """Processes raw button transitions into debounced single/double tap gestures."""

    def __init__(
        self,
        debounce_window_ms: int = 50,
        double_tap_window_ms: int = 350,
    ) -> None:
        self._debounce_window = timedelta(milliseconds=debounce_window_ms)
        self._double_tap_window = timedelta(milliseconds=double_tap_window_ms)
        self._active_presses: dict[str, _PressState] = {}
        self._last_transition: dict[str, datetime] = {}
        self._pending_taps: dict[str, _TapState] = {}

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

        duration_ms = round((timestamp - active.started_at).total_seconds() * 1000)

        pending = self._pending_taps.get(button_id)
        if pending is None:
            # First valid tap: keep pending and wait for second tap in configured window.
            self._pending_taps[button_id] = _TapState(
                tap_count=1,
                first_tap_at=timestamp,
                last_tap_duration_ms=duration_ms,
            )
            return None

        if timestamp - pending.first_tap_at <= self._double_tap_window:
            self._pending_taps.pop(button_id, None)
            return self._build_event(
                button_id=button_id,
                timestamp=timestamp,
                gesture="double",
                tap_count=2,
                duration_ms=duration_ms,
            )

        # Outside window: emit previous pending single tap now and start a new pending tap.
        single_event = self._build_event(
            button_id=button_id,
            timestamp=timestamp,
            gesture="single",
            tap_count=pending.tap_count,
            duration_ms=pending.last_tap_duration_ms,
        )
        self._pending_taps[button_id] = _TapState(
            tap_count=1,
            first_tap_at=timestamp,
            last_tap_duration_ms=duration_ms,
        )
        return single_event

    def collect_timeout_events(self, at: datetime | None = None) -> list[HardwareEvent]:
        """Emit single tap events for all buttons whose double tap window has expired."""
        timestamp = at or datetime.now(tz=timezone.utc)
        events: list[HardwareEvent] = []

        for button_id, pending in list(self._pending_taps.items()):
            if timestamp - pending.first_tap_at < self._double_tap_window:
                continue
            self._pending_taps.pop(button_id, None)
            events.append(
                self._build_event(
                    button_id=button_id,
                    timestamp=timestamp,
                    gesture="single",
                    tap_count=pending.tap_count,
                    duration_ms=pending.last_tap_duration_ms,
                )
            )

        return events

    def _build_event(
        self,
        button_id: str,
        timestamp: datetime,
        gesture: str,
        tap_count: int,
        duration_ms: int,
    ) -> HardwareEvent:
        return HardwareEvent(
            event_type="input.control",
            source=f"hid:{button_id}",
            value={
                "gesture": gesture,
                "tap_count": tap_count,
                "duration_ms": duration_ms,
                "source": f"hid:{button_id}",
            },
            unit=None,
            timestamp=timestamp,
        )

    def _is_debounced(self, button_id: str, timestamp: datetime) -> bool:
        previous = self._last_transition.get(button_id)
        if previous is None:
            return False
        return timestamp - previous < self._debounce_window
