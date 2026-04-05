from __future__ import annotations

from ..event_bus import RuntimeEvent, SharedEventBus
from .events import HardwareEvent


class HardwareEventPublisher:
    """Publishes normalized hardware events onto the runtime event bus."""

    def __init__(self, event_bus: SharedEventBus) -> None:
        self._event_bus = event_bus

    def publish(self, event: HardwareEvent) -> None:
        self._event_bus.publish(RuntimeEvent.HARDWARE_EVENT, event.as_payload())
