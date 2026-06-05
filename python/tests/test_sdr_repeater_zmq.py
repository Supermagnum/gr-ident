"""Compatibility with SDR-repeater zeromq-messages.md (rev 1.2)."""

from __future__ import annotations

import json
import unittest

from grident.preamble import PreambleField
from grident.tx_control import TxControlState, parse_tx_control_message
from grident.zmq_protocol import (
    GRIDENT_PREAMBLE_TOPIC,
    format_preamble_result_json,
    parse_preamble_result_json,
    preamble_result_from_field,
    preamble_result_topic,
)


class SdrRepeaterPreambleJsonTests(unittest.TestCase):
    def test_mode_20_example(self) -> None:
        body = format_preamble_result_json(20, digital=False, encrypted=False, metadata_present=False)
        parsed = parse_preamble_result_json(body)
        self.assertEqual(parsed.mode_id, 20)
        self.assertFalse(parsed.digital)
        self.assertEqual(
            json.loads(body),
            {
                "mode_id": 20,
                "digital": False,
                "encrypted": False,
                "metadata_present": False,
            },
        )

    def test_mode_300_example(self) -> None:
        body = format_preamble_result_json(300, digital=True, encrypted=False, metadata_present=False)
        parsed = parse_preamble_result_json(body)
        self.assertEqual(parsed.mode_id, 300)
        self.assertTrue(parsed.digital)

    def test_field_roundtrip(self) -> None:
        field = PreambleField(mode_id=110, digital=True, encrypted=False, metadata_present=False)
        msg = preamble_result_from_field(field)
        body = format_preamble_result_json(
            msg.mode_id,
            digital=msg.digital,
            encrypted=msg.encrypted,
            metadata_present=msg.metadata_present,
        )
        self.assertEqual(parse_preamble_result_json(body), msg)


class SdrRepeaterTopicTests(unittest.TestCase):
    def test_default_topic(self) -> None:
        self.assertEqual(preamble_result_topic(), GRIDENT_PREAMBLE_TOPIC)

    def test_module_topics(self) -> None:
        self.assertEqual(preamble_result_topic("B"), "grident.B")
        self.assertEqual(preamble_result_topic("a"), "grident.A")

    def test_invalid_module(self) -> None:
        with self.assertRaises(ValueError):
            preamble_result_topic("BOTH")


class SdrRepeaterTxControlTests(unittest.TestCase):
    """Section 6.2 accepted payloads."""

    def test_tx_on_payloads(self) -> None:
        for payload in (
            b"PTT_ON",
            b"TX",
            b"KEYDOWN",
            b"1",
            b"ON",
            b"SOT",
            b'{"ptt": true}',
        ):
            with self.subTest(payload=payload):
                self.assertEqual(parse_tx_control_message(payload), TxControlState.ON)

    def test_tx_off_payloads(self) -> None:
        for payload in (
            b"PTT_OFF",
            b"RX",
            b"KEYUP",
            b"0",
            b"OFF",
            b"EOT",
            b'{"ptt": false}',
        ):
            with self.subTest(payload=payload):
                self.assertEqual(parse_tx_control_message(payload), TxControlState.OFF)


if __name__ == "__main__":
    unittest.main()
