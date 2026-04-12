from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .connection_manager import ConnectionManager, ConnectionState
from .translator import TransportPayload

# Seeded from Backend/backend_gatt_server.py (Nordic UART style service)
TEXT_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
TEXT_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
TEXT_TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


@dataclass
class GATTCharacteristic:
    uuid: str
    can_read: bool = False
    can_write: bool = False
    can_notify: bool = False
    value: bytes = b""


@dataclass
class GATTService:
    uuid: str
    characteristics: dict[str, GATTCharacteristic] = field(default_factory=dict)


class BluetoothAdapter:
    """Unified GATT server/client adapter for runtime command frames."""

    def __init__(self, connection_manager: ConnectionManager, adapter_name: str = "bluetooth") -> None:
        self._connection_manager = connection_manager
        self._adapter_name = adapter_name
        self._services: dict[str, GATTService] = {}
        self._listeners: list[Callable[[TransportPayload], None]] = []
        self._connected_peer: str | None = None

        uart_service = GATTService(
            uuid=TEXT_SERVICE_UUID,
            characteristics={
                TEXT_RX_UUID: GATTCharacteristic(TEXT_RX_UUID, can_write=True),
                TEXT_TX_UUID: GATTCharacteristic(TEXT_TX_UUID, can_notify=True, can_read=True),
            },
        )
        self.register_service(uart_service)

    def register_service(self, service: GATTService) -> None:
        self._services[service.uuid] = service

    def connect_peer(self, peer_id: str) -> None:
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.CONNECTING,
            reason=f"connecting to {peer_id}",
        )
        self._connected_peer = peer_id
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.CONNECTED,
            reason=f"connected to {peer_id}",
        )

    def disconnect_peer(self, reason: str = "manual disconnect") -> None:
        self._connected_peer = None
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.DISCONNECTED,
            reason=reason,
        )

    def on_payload(self, callback: Callable[[TransportPayload], None]) -> None:
        self._listeners.append(callback)

    def receive_from_gatt_write(self, payload: TransportPayload) -> None:
        """Server-side hook invoked when a remote client writes to RX characteristic."""
        for listener in list(self._listeners):
            listener(payload)

    def send_notification(self, payload: TransportPayload) -> None:
        """Server-side notify operation over TX characteristic."""
        if not self._connected_peer:
            self._connection_manager.set_state(
                self._adapter_name,
                ConnectionState.DEGRADED,
                reason="notification dropped; no active peer",
            )
            return
        for listener in list(self._listeners):
            listener(payload)

    def health(self) -> dict[str, str | int | None]:
        return {
            "adapter": self._adapter_name,
            "mode": "gatt_server_client",
            "peer": self._connected_peer,
            "services": len(self._services),
            "listeners": len(self._listeners),
        }
