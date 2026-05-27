"""ZeroMQ TX/PTT control helpers for gr-ident transmit flowgraphs."""

from __future__ import annotations

import json
from enum import Enum

# LinHT GUI / zmq_proxy PTT endpoint (M17-Project/LinHT-utils).
LINHT_PTT_ENDPOINT = "ipc:///tmp/ptt_msg"
LINHT_FG_AUX_ENDPOINT = "ipc:///tmp/fg_aux_data_in"


class TxControlState(str, Enum):
    ON = "on"
    OFF = "off"


def format_linht_pmt(symbol: str) -> bytes:
    """Build a LinHT GNU Radio PMT string frame (0x02, uint16 BE length, payload)."""
    body = symbol.encode("ascii")
    return bytes([0x02, (len(body) >> 8) & 0xFF, len(body) & 0xFF]) + body


def parse_linht_pmt(payload: bytes) -> TxControlState | None:
    """Parse LinHT PMT SOT/EOT bytes."""
    if len(payload) < 3 or payload[0] != 0x02:
        return None
    sym_len = (payload[1] << 8) | payload[2]
    if len(payload) < 3 + sym_len:
        return None
    sym = payload[3 : 3 + sym_len].decode("ascii", errors="replace")
    if sym == "SOT":
        return TxControlState.ON
    if sym == "EOT":
        return TxControlState.OFF
    return None


def parse_tx_control_message(payload: bytes | str) -> TxControlState | None:
    """Parse a TX/PTT control message (matches C++ parse_tx_control_message)."""
    if isinstance(payload, bytes):
        linht = parse_linht_pmt(payload)
        if linht is not None:
            return linht
        text = payload.decode("utf-8", errors="replace").strip()
    else:
        text = payload.strip()

    if not text:
        return None

    if text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
        for key in ("ptt", "tx", "key"):
            if key in data:
                return TxControlState.ON if bool(data[key]) else TxControlState.OFF
        return None

    upper = text.upper()
    if upper in {"1", "ON", "TX", "PTT", "PTT_ON", "KEYDOWN", "KEY_DOWN", "SOT"}:
        return TxControlState.ON
    if upper in {"0", "OFF", "RX", "PTT_OFF", "KEYUP", "KEY_UP", "EOT"}:
        return TxControlState.OFF
    return None


def format_tx_control_message(state: TxControlState, *, as_json: bool = True) -> bytes:
    """Build a gr-ident control payload for ZmqTxControlSub (grident profile)."""
    if as_json:
        return json.dumps({"ptt": state == TxControlState.ON}, separators=(",", ":")).encode("ascii")
    return b"PTT_ON" if state == TxControlState.ON else b"PTT_OFF"


def send_tx_control(
    endpoint: str,
    state: TxControlState,
    *,
    profile: str = "linht",
    topic: str = "grident.tx",
    bind: bool = False,
) -> None:
    """Publish one TX/PTT control message (requires pyzmq).

    profile:
      linht  -- single-part PMT SOT/EOT (default endpoint ipc:///tmp/ptt_msg)
      grident -- multipart [topic, JSON or plain text]
    """
    import zmq

    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    if bind:
        pub.bind(endpoint)
    else:
        pub.connect(endpoint)

    if profile == "linht":
        symbol = "SOT" if state == TxControlState.ON else "EOT"
        pub.send(format_linht_pmt(symbol))
    else:
        pub.send_multipart([topic.encode("ascii"), format_tx_control_message(state)])
    pub.close(0)
