from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class OverlaySyncContract:
    """Contract between streamed content overlays and onboard HUD layers."""

    contract_version: str = "1.0"
    coordinate_space: str = "normalized"
    safe_area: dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}
    )
    z_order: list[str] = field(default_factory=lambda: ["streamed-scene", "streamed-overlay", "onboard-hud"])
    last_synced_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def sync(self, streamed_overlay_bounds: dict[str, float], onboard_hud_bounds: dict[str, float]) -> dict[str, Any]:
        self.last_synced_at = datetime.now(tz=timezone.utc).isoformat()
        return {
            "contract_version": self.contract_version,
            "coordinate_space": self.coordinate_space,
            "safe_area": self.safe_area,
            "z_order": self.z_order,
            "streamed_overlay_bounds": streamed_overlay_bounds,
            "onboard_hud_bounds": onboard_hud_bounds,
            "last_synced_at": self.last_synced_at,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "coordinate_space": self.coordinate_space,
            "safe_area": dict(self.safe_area),
            "z_order": list(self.z_order),
            "last_synced_at": self.last_synced_at,
        }
