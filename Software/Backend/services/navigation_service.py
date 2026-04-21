from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.sensor_service import SensorService


class NavigationService:
    """Build minimal navigation snapshots from available onboard sensor streams."""

    def __init__(self, sensor_service: SensorService):
        self._sensor_service = sensor_service

    def _to_float(self, value: Any) -> float | None:
        if isinstance(value, (float, int)):
            return float(value)
        return None

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_current_snapshot(self) -> dict[str, Any]:
        sensor_snapshot = self._sensor_service.get_snapshot()
        mpu6050 = sensor_snapshot.get("mpu6050", {}) if isinstance(sensor_snapshot, dict) else {}

        gyro = mpu6050.get("gyroscope_dps", {}) if isinstance(mpu6050, dict) else {}
        orientation = self._to_float(gyro.get("z") if isinstance(gyro, dict) else None)
        heading = self._to_float(gyro.get("x") if isinstance(gyro, dict) else None)

        timestamp = None
        if isinstance(mpu6050, dict):
            timestamp = mpu6050.get("updated_at")
        if not isinstance(timestamp, str) or not timestamp:
            timestamp = sensor_snapshot.get("updated_at") if isinstance(sensor_snapshot, dict) else None
        if not isinstance(timestamp, str) or not timestamp:
            timestamp = self._utc_now()

        return {
            "heading": heading,
            "orientation": orientation,
            "timestamp": timestamp,
            "source": {
                "provider": "backend.sensor_service",
                "sensor": "mpu6050",
                "event_types": ["navigation.heading", "navigation.orientation"],
            },
        }
