from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .hid import HIDInputAdapter
from .publisher import HardwareEventPublisher


class HIDRuntimeEventPump:
    """Runtime tick helper that ingests HID transitions and flushes pending timeouts."""

    def __init__(
        self,
        adapter: HIDInputAdapter,
        publisher: HardwareEventPublisher,
    ) -> None:
        self._adapter = adapter
        self._publisher = publisher

    def process_transition(
        self,
        button_id: str,
        pressed: bool,
        at: datetime | None = None,
    ) -> None:
        event = self._adapter.ingest_transition(button_id=button_id, pressed=pressed, at=at)
        if event is not None:
            self._publisher.publish(event)

    def tick(
        self,
        transitions: Iterable[tuple[str, bool]] = (),
        at: datetime | None = None,
    ) -> None:
        """Process all raw transitions for this poll tick and flush timed-out singles."""
        timestamp = at or datetime.now(tz=timezone.utc)

        for button_id, pressed in transitions:
            event = self._adapter.ingest_transition(button_id=button_id, pressed=pressed, at=timestamp)
            if event is not None:
                self._publisher.publish(event)

        for timeout_event in self._adapter.collect_timeout_events(at=timestamp):
            self._publisher.publish(timeout_event)
