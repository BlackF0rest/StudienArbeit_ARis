from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from .events import HardwareEvent


class SensorAdapter(Protocol):
    """Protocol for all sensor adapters to enable future device expansion."""

    name: str

    def sample(self, at: datetime | None = None) -> list[HardwareEvent]:
        """Return normalized events from one sampling cycle."""


@dataclass(frozen=True)
class BME280Reading:
    temperature_c: float
    humidity_percent: float
    pressure_hpa: float


@dataclass(frozen=True)
class GyroReading:
    orientation_deg: float
    heading_deg: float


class BME280Adapter:
    name = "bme280"

    def __init__(self, reader: Callable[[], BME280Reading]) -> None:
        self._reader = reader

    def sample(self, at: datetime | None = None) -> list[HardwareEvent]:
        reading = self._reader()
        timestamp = at or datetime.now(tz=timezone.utc)
        return [
            HardwareEvent(
                event_type="battery.status",
                source=self.name,
                value=reading.pressure_hpa,
                unit="hPa",
                timestamp=timestamp,
            ),
            HardwareEvent(
                event_type="temperature.ambient",
                source=self.name,
                value=reading.temperature_c,
                unit="C",
                timestamp=timestamp,
            ),
            HardwareEvent(
                event_type="humidity.relative",
                source=self.name,
                value=reading.humidity_percent,
                unit="%",
                timestamp=timestamp,
            ),
        ]


class GyroAdapter:
    name = "gyro"

    def __init__(self, reader: Callable[[], GyroReading]) -> None:
        self._reader = reader

    def sample(self, at: datetime | None = None) -> list[HardwareEvent]:
        reading = self._reader()
        timestamp = at or datetime.now(tz=timezone.utc)
        return [
            HardwareEvent(
                event_type="navigation.orientation",
                source=self.name,
                value=reading.orientation_deg,
                unit="deg",
                timestamp=timestamp,
            ),
            HardwareEvent(
                event_type="navigation.heading",
                source=self.name,
                value=reading.heading_deg,
                unit="deg",
                timestamp=timestamp,
            ),
        ]
