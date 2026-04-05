from __future__ import annotations

from collections import defaultdict
from typing import Callable

from .connection_manager import ConnectionManager, ConnectionState
from .translator import TransportPayload


class WiFiAdapter:
    """WiFi adapter for PC interface traffic and external service routing."""

    def __init__(self, connection_manager: ConnectionManager, adapter_name: str = "wifi") -> None:
        self._connection_manager = connection_manager
        self._adapter_name = adapter_name
        self._pc_clients: set[str] = set()
        self._external_services: dict[str, str] = {}
        self._listeners: list[Callable[[TransportPayload], None]] = []
        self._sent_counters: dict[str, int] = defaultdict(int)

    def connect(self) -> None:
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.CONNECTED,
            reason="wifi link established",
        )

    def disconnect(self, reason: str = "wifi link dropped") -> None:
        self._connection_manager.set_state(
            self._adapter_name,
            ConnectionState.DISCONNECTED,
            reason=reason,
        )

    def register_pc_client(self, client_id: str) -> None:
        self._pc_clients.add(client_id)

    def unregister_pc_client(self, client_id: str) -> None:
        self._pc_clients.discard(client_id)

    def register_external_service(self, service_name: str, endpoint: str) -> None:
        self._external_services[service_name] = endpoint

    def on_payload(self, callback: Callable[[TransportPayload], None]) -> None:
        self._listeners.append(callback)

    def receive(self, payload: TransportPayload) -> None:
        for listener in list(self._listeners):
            listener(payload)

    def send_to_pc(self, client_id: str, payload: TransportPayload) -> bool:
        if client_id not in self._pc_clients:
            self._connection_manager.set_state(
                self._adapter_name,
                ConnectionState.DEGRADED,
                reason=f"unknown pc client {client_id}",
            )
            return False
        self._sent_counters[f"pc:{client_id}"] += 1
        return True

    def send_to_service(self, service_name: str, payload: TransportPayload) -> bool:
        if service_name not in self._external_services:
            self._connection_manager.set_state(
                self._adapter_name,
                ConnectionState.DEGRADED,
                reason=f"unknown service {service_name}",
            )
            return False
        self._sent_counters[f"service:{service_name}"] += 1
        return True

    def health(self) -> dict[str, object]:
        return {
            "adapter": self._adapter_name,
            "pc_clients": len(self._pc_clients),
            "external_services": len(self._external_services),
            "sent_counters": dict(self._sent_counters),
        }
