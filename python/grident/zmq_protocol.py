"""ZeroMQ wire-format helpers aligned with gr-ident and SDR-repeater conventions.

Canonical repeater integration spec (external):
https://github.com/Supermagnum/SDR-repeater/blob/main/zeromq-messages.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

# gr-ident default endpoints (lab / K3 flowgraphs)
GRIDENT_PREAMBLE_PUB_DEFAULT = "tcp://127.0.0.1:5560"
GRIDENT_TX_CONTROL_DEFAULT = "tcp://127.0.0.1:5561"
GRIDENT_IQ_PUSH_PULL_DEFAULT = "tcp://127.0.0.1:5555"

# SDR-repeater suggested endpoints (Section 6, zeromq-messages.md rev 1.2)
REPEATER_PREAMBLE_PUB_SUGGESTED = "tcp://127.0.0.1:5560"
REPEATER_PREAMBLE_PUB_IPC = "ipc:///run/ht-module/grident"
REPEATER_TX_CONTROL_SUGGESTED = "tcp://127.0.0.1:5561"

# Repeater native (ht-module-daemon) — not implemented by gr-ident blocks
REPEATER_IQ_IPC_TEMPLATE = "ipc:///run/ht-module/iq_{module}"
REPEATER_TX_IQ_IPC_TEMPLATE = "ipc:///run/ht-module/tx_{module}"
REPEATER_CTRL_IPC = "ipc:///run/ht-module/ctrl"
REPEATER_STATUS_IPC = "ipc:///run/ht-module/status"

GRIDENT_TX_TOPIC = "grident.tx"
GRIDENT_PREAMBLE_TOPIC = "grident"
GRIDENT_PREAMBLE_TOPIC_PREFIX = "grident."


@dataclass(frozen=True)
class PreambleResultMessage:
    """Decoded primary preamble fields for mode router subscribers."""

    mode_id: int
    digital: bool
    encrypted: bool
    metadata_present: bool


def preamble_result_topic(module: str | None = None, *, band: str | None = None) -> str:
    """
    ZMQ topic for PreambleResultZmqPub (multipart frame 0).

    module: repeater slot letter A-D (yields grident.A, ...)
    band: optional suffix when unambiguous (yields grident.70cm, ...)
    """
    if module is not None:
        letter = module.strip().upper()
        if len(letter) != 1 or letter not in "ABCD":
            raise ValueError(f"module must be A, B, C, or D, got {module!r}")
        return f"{GRIDENT_PREAMBLE_TOPIC_PREFIX}{letter}"
    if band is not None:
        slug = band.strip().lower().replace(" ", "")
        if not slug:
            raise ValueError("band must be non-empty")
        return f"{GRIDENT_PREAMBLE_TOPIC_PREFIX}{slug}"
    return GRIDENT_PREAMBLE_TOPIC


def format_preamble_result_json(
    mode_id: int,
    *,
    digital: bool,
    encrypted: bool = False,
    metadata_present: bool = False,
) -> str:
    """UTF-8 JSON body for PreambleResultZmqPub (SDR-repeater Section 6.1)."""
    if not 0 <= mode_id <= 511:
        raise ValueError(f"mode_id must be 0..511, got {mode_id}")
    payload = {
        "mode_id": mode_id,
        "digital": digital,
        "encrypted": encrypted,
        "metadata_present": metadata_present,
    }
    return json.dumps(payload, separators=(",", ":"))


def parse_preamble_result_json(payload: str | bytes) -> PreambleResultMessage:
    """Parse preamble JSON from ZMQ multipart frame 1."""
    if isinstance(payload, bytes):
        text = payload.decode("utf-8")
    else:
        text = payload
    data: dict[str, Any] = json.loads(text)
    return PreambleResultMessage(
        mode_id=int(data["mode_id"]),
        digital=bool(data["digital"]),
        encrypted=bool(data["encrypted"]),
        metadata_present=bool(data["metadata_present"]),
    )


def preamble_result_from_field(field: Any) -> PreambleResultMessage:
    """Build message from grident.preamble.PreambleField."""
    return PreambleResultMessage(
        mode_id=int(field.mode_id),
        digital=bool(field.digital),
        encrypted=bool(field.encrypted),
        metadata_present=bool(field.metadata_present),
    )


def publish_preamble_result(
    message: PreambleResultMessage | Any,
    *,
    endpoint: str = GRIDENT_PREAMBLE_PUB_DEFAULT,
    topic: str | None = None,
    module: str | None = None,
    bind: bool = True,
) -> None:
    """Publish one preamble decode result (multipart [topic, JSON]). Requires pyzmq."""
    import zmq

    if not isinstance(message, PreambleResultMessage):
        message = preamble_result_from_field(message)

    topic_name = topic if topic is not None else preamble_result_topic(module)
    body = format_preamble_result_json(
        message.mode_id,
        digital=message.digital,
        encrypted=message.encrypted,
        metadata_present=message.metadata_present,
    )

    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    if bind:
        pub.bind(endpoint)
    else:
        pub.connect(endpoint)
    pub.send_multipart([topic_name.encode("ascii"), body.encode("utf-8")])
    pub.close(0)


def subscribe_preamble_results(
    endpoint: str = GRIDENT_PREAMBLE_PUB_DEFAULT,
    *,
    topic_filter: str = GRIDENT_PREAMBLE_TOPIC,
    bind: bool = False,
):
    """
    Context manager yielding (topic: str, PreambleResultMessage) from SUB socket.

    Use topic_filter='grident' to receive grident, grident.A, grident.B, ... (ZMQ prefix).
    """
    import zmq

    class _Iterator:
        def __init__(self) -> None:
            self._ctx = zmq.Context.instance()
            self._sub = self._ctx.socket(zmq.SUB)
            if bind:
                self._sub.bind(endpoint)
            else:
                self._sub.connect(endpoint)
            self._sub.setsockopt_string(zmq.SUBSCRIBE, topic_filter)

        def __iter__(self):
            return self

        def __next__(self) -> tuple[str, PreambleResultMessage]:
            topic_b, payload = self._sub.recv_multipart()
            return topic_b.decode("ascii"), parse_preamble_result_json(payload)

        def close(self) -> None:
            self._sub.close(0)

    return _Iterator()
