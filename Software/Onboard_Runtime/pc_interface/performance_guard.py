from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..comm.connection_manager import ConnectionManager, ConnectionState


@dataclass
class GuardrailThresholds:
    min_bandwidth_mbps: float = 8.0
    max_frame_drop_ratio: float = 0.12


class StreamPerformanceGuard:
    """Bandwidth/frame-drop guardrails and fallback display mode manager."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        thresholds: GuardrailThresholds | None = None,
        adapter_name: str = "pc-link",
    ) -> None:
        self._connection_manager = connection_manager
        self._thresholds = thresholds or GuardrailThresholds()
        self._adapter_name = adapter_name
        self._bandwidth_samples: deque[float] = deque(maxlen=60)
        self._frame_drop_samples: deque[float] = deque(maxlen=60)
        self._onboard_only_mode = False
        self._last_updated = datetime.now(tz=timezone.utc).isoformat()

    def record_bandwidth_mbps(self, value: float) -> None:
        self._bandwidth_samples.append(max(0.0, value))
        self._last_updated = datetime.now(tz=timezone.utc).isoformat()
        self._evaluate()

    def record_frame_drop_ratio(self, value: float) -> None:
        self._frame_drop_samples.append(min(max(value, 0.0), 1.0))
        self._last_updated = datetime.now(tz=timezone.utc).isoformat()
        self._evaluate()

    def _evaluate(self) -> None:
        avg_bandwidth = self._average(self._bandwidth_samples)
        avg_drop_ratio = self._average(self._frame_drop_samples)

        should_fallback = (
            avg_bandwidth is not None
            and avg_drop_ratio is not None
            and (
                avg_bandwidth < self._thresholds.min_bandwidth_mbps
                or avg_drop_ratio > self._thresholds.max_frame_drop_ratio
            )
        )

        if should_fallback and not self._onboard_only_mode:
            self._onboard_only_mode = True
            self._connection_manager.set_state(
                self._adapter_name,
                ConnectionState.DEGRADED,
                reason="stream guardrails triggered onboard-only mode",
            )
        elif not should_fallback and self._onboard_only_mode:
            self._onboard_only_mode = False
            self._connection_manager.set_state(
                self._adapter_name,
                ConnectionState.CONNECTED,
                reason="stream guardrails restored pc streaming",
            )

    def snapshot(self) -> dict[str, Any]:
        return {
            "avg_bandwidth_mbps": self._average(self._bandwidth_samples),
            "avg_frame_drop_ratio": self._average(self._frame_drop_samples),
            "thresholds": {
                "min_bandwidth_mbps": self._thresholds.min_bandwidth_mbps,
                "max_frame_drop_ratio": self._thresholds.max_frame_drop_ratio,
            },
            "onboard_only_mode": self._onboard_only_mode,
            "last_updated": self._last_updated,
        }

    @staticmethod
    def _average(samples: deque[float]) -> float | None:
        if not samples:
            return None
        return round(sum(samples) / len(samples), 4)
