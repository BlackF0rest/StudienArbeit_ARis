from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..comm.connection_manager import ConnectionManager, ConnectionState


@dataclass
class WiFiSession:
    session_id: str
    pc_id: str
    connected_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    last_seen_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    active: bool = True


class PCWiFiSessionManager:
    """Tracks WiFi sessions for PC link clients."""

    def __init__(self, connection_manager: ConnectionManager, adapter_name: str = "pc-link") -> None:
        self._connection_manager = connection_manager
        self._adapter_name = adapter_name
        self._sessions: dict[str, WiFiSession] = {}

    def start_session(self, session_id: str, pc_id: str) -> WiFiSession:
        session = WiFiSession(session_id=session_id, pc_id=pc_id)
        self._sessions[session_id] = session
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.CONNECTED,
            reason=f"pc session started ({pc_id})",
        )
        return session

    def touch_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.last_seen_at = datetime.now(tz=timezone.utc).isoformat()

    def end_session(self, session_id: str, reason: str = "pc session ended") -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.active = False
        session.last_seen_at = datetime.now(tz=timezone.utc).isoformat()

        if not self.active_sessions:
            self._connection_manager.set_state(
                self._adapter_name,
                ConnectionState.DISCONNECTED,
                reason=reason,
            )

    @property
    def active_sessions(self) -> list[WiFiSession]:
        return [session for session in self._sessions.values() if session.active]

    def health(self) -> dict[str, Any]:
        active = self.active_sessions
        return {
            "adapter": self._adapter_name,
            "active_sessions": len(active),
            "sessions": [
                {
                    "session_id": session.session_id,
                    "pc_id": session.pc_id,
                    "connected_at": session.connected_at,
                    "last_seen_at": session.last_seen_at,
                }
                for session in active
            ],
        }
