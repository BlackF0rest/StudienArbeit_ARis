from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..event_bus import EventMessage, RuntimeEvent, SharedEventBus


@dataclass
class _BaseSubscription:
    event_bus: SharedEventBus
    interested_types: set[str]
    received_events: list[dict[str, Any]] = field(default_factory=list)

    def attach(self) -> None:
        self.event_bus.subscribe(RuntimeEvent.HARDWARE_EVENT, self._on_hardware_event)

    def detach(self) -> None:
        self.event_bus.unsubscribe(RuntimeEvent.HARDWARE_EVENT, self._on_hardware_event)

    def _on_hardware_event(self, message: EventMessage) -> None:
        event_type = str(message.payload.get("event_type", ""))
        if event_type in self.interested_types:
            self.received_events.append(message.payload)


class BasicHUDSubscription(_BaseSubscription):
    def __init__(self, event_bus: SharedEventBus) -> None:
        super().__init__(
            event_bus=event_bus,
            interested_types={
                "battery.status",
                "temperature.ambient",
                "humidity.relative",
            },
        )


class NavigationSubscription(_BaseSubscription):
    def __init__(self, event_bus: SharedEventBus) -> None:
        super().__init__(
            event_bus=event_bus,
            interested_types={
                "navigation.orientation",
                "navigation.heading",
            },
        )


class TeleprompterSubscription(_BaseSubscription):
    def __init__(self, event_bus: SharedEventBus) -> None:
        super().__init__(
            event_bus=event_bus,
            interested_types={
                "input.control",
            },
        )
