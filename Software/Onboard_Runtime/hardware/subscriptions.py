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
            normalized_payload = dict(message.payload)
            if event_type == "input.control":
                normalized_payload["value"] = _normalize_input_control_value(
                    message.payload.get("value")
                )
            self.received_events.append(normalized_payload)


def _normalize_input_control_value(value: Any) -> dict[str, Any]:
    """Normalize `input.control` values to the canonical gesture + switch contract.

    Transition phase behavior:
    - Prefer `gesture` when already present.
    - If only legacy `press` data is present (e.g. `short_press`/`long_press`), map it to `gesture`.
    - Prefer `switch_state` when present and valid (`high`/`low`).
    - If `switch_state` is absent in legacy payloads, derive a stable fallback (`low`).
    - Always return a payload that writes `gesture` and `switch_state` as canonical fields.
    """
    if not isinstance(value, dict):
        return {"switch_state": "low"}

    normalized = dict(value)
    gesture = normalized.get("gesture")
    if not (isinstance(gesture, str) and gesture):
        legacy_press = normalized.get("press")
        if isinstance(legacy_press, str):
            legacy_to_gesture = {
                "short_press": "single",
                "long_press": "double",
            }
            mapped = legacy_to_gesture.get(legacy_press, legacy_press)
            if mapped:
                normalized["gesture"] = mapped

    switch_state = normalized.get("switch_state")
    if switch_state not in {"high", "low"}:
        normalized["switch_state"] = "low"

    return normalized


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
