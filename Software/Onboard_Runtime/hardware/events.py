from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class HardwareEvent:
    """Normalized schema for all hardware-originated events."""

    event_type: str
    source: str
    value: Any
    unit: str | None
    timestamp: datetime

    @classmethod
    def now(
        cls,
        event_type: str,
        source: str,
        value: Any,
        unit: str | None = None,
    ) -> "HardwareEvent":
        return cls(
            event_type=event_type,
            source=source,
            value=value,
            unit=unit,
            timestamp=datetime.now(tz=timezone.utc),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "source": self.source,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
        }
