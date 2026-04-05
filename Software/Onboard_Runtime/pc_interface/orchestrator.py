from __future__ import annotations

from typing import Any

from ..comm.connection_manager import ConnectionManager
from .overlay_sync import OverlaySyncContract
from .performance_guard import StreamPerformanceGuard
from .pixel_streaming import PixelStreamingOrchestrator
from .wifi_session_manager import PCWiFiSessionManager


class PCInterfaceOrchestrator:
    """Unified integration surface for PC-link connectivity and streaming."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self.wifi_sessions = PCWiFiSessionManager(connection_manager)
        self.pixel_streaming = PixelStreamingOrchestrator()
        self.overlay_sync = OverlaySyncContract()
        self.performance_guard = StreamPerformanceGuard(connection_manager)

    def health(self) -> dict[str, Any]:
        return {
            "wifi_sessions": self.wifi_sessions.health(),
            "pixel_streaming": self.pixel_streaming.snapshot(),
            "overlay_sync": self.overlay_sync.snapshot(),
            "performance_guard": self.performance_guard.snapshot(),
        }

    def diagnostic_panel(self) -> dict[str, Any]:
        return {
            "pc_link": {
                "active": bool(self.wifi_sessions.active_sessions),
                "sessions": self.wifi_sessions.health()["sessions"],
            },
            "stream_metrics": {
                **self.pixel_streaming.snapshot(),
                **self.performance_guard.snapshot(),
            },
            "overlay_contract": self.overlay_sync.snapshot(),
        }
