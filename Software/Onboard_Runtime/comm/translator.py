from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class TransportPayload:
    """Transport-agnostic wire envelope used by Bluetooth/USB/WiFi adapters."""

    capability: str
    op: str
    payload: dict[str, Any]
    source: str
    qos: int = 0
    msg_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None
    timestamp_ms: int = field(
        default_factory=lambda: int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    )


@dataclass(frozen=True)
class InternalCommand:
    """Normalized runtime command schema consumed by internal services."""

    command_id: str
    command_type: str
    target: str
    params: dict[str, Any]
    source: str
    correlation_id: str | None = None
    qos: int = 0
    created_at_ms: int = field(
        default_factory=lambda: int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    )


class TransportTranslator:
    """Maps transport payloads to the internal command schema and back."""

    def to_internal(self, transport: TransportPayload) -> InternalCommand:
        return InternalCommand(
            command_id=transport.msg_id,
            command_type=transport.op,
            target=transport.capability,
            params=dict(transport.payload),
            source=transport.source,
            correlation_id=transport.correlation_id,
            qos=transport.qos,
            created_at_ms=transport.timestamp_ms,
        )

    def to_transport(self, command: InternalCommand) -> TransportPayload:
        return TransportPayload(
            msg_id=command.command_id,
            capability=command.target,
            op=command.command_type,
            payload=dict(command.params),
            source=command.source,
            correlation_id=command.correlation_id,
            qos=command.qos,
            timestamp_ms=command.created_at_ms,
        )
