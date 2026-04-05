from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class RuntimeEvent(str, Enum):
    BUTTON_PRESS = "button_press"
    SENSOR_UPDATE = "sensor_update"
    TELEPROMPTER_UPDATE = "teleprompter_update"
    CONNECTION_STATUS = "connection_status"


@dataclass
class EventMessage:
    event: RuntimeEvent
    payload: dict[str, Any]


class SharedEventBus:
    """Simple in-process pub/sub bus for cross-module communication."""

    def __init__(self) -> None:
        self._handlers: dict[RuntimeEvent, list[Callable[[EventMessage], None]]] = defaultdict(
            list
        )

    def subscribe(
        self, event: RuntimeEvent, handler: Callable[[EventMessage], None]
    ) -> None:
        self._handlers[event].append(handler)

    def unsubscribe(
        self, event: RuntimeEvent, handler: Callable[[EventMessage], None]
    ) -> None:
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def publish(self, event: RuntimeEvent, payload: dict[str, Any]) -> None:
        message = EventMessage(event=event, payload=payload)
        for handler in list(self._handlers[event]):
            handler(message)
