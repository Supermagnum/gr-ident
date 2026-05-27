import unittest

from grident.tx_control import (
    TxControlState,
    format_linht_pmt,
    format_tx_control_message,
    parse_linht_pmt,
    parse_tx_control_message,
)


class TestTxControl(unittest.TestCase):
    def test_plain_on_off(self):
        self.assertEqual(parse_tx_control_message(b"PTT_ON"), TxControlState.ON)
        self.assertEqual(parse_tx_control_message("ptt_off"), TxControlState.OFF)
        self.assertEqual(parse_tx_control_message("TX"), TxControlState.ON)
        self.assertEqual(parse_tx_control_message("RX"), TxControlState.OFF)

    def test_json(self):
        self.assertEqual(parse_tx_control_message('{"ptt": true}'), TxControlState.ON)
        self.assertEqual(parse_tx_control_message('{"ptt": false}'), TxControlState.OFF)
        self.assertEqual(parse_tx_control_message('{"tx": 0}'), TxControlState.OFF)

    def test_format_roundtrip(self):
        for state in TxControlState:
            payload = format_tx_control_message(state, as_json=True)
            self.assertEqual(parse_tx_control_message(payload), state)

    def test_linht_pmt(self):
        self.assertEqual(parse_linht_pmt(format_linht_pmt("SOT")), TxControlState.ON)
        self.assertEqual(parse_linht_pmt(format_linht_pmt("EOT")), TxControlState.OFF)
        self.assertEqual(parse_tx_control_message(format_linht_pmt("SOT")), TxControlState.ON)
        self.assertEqual(parse_tx_control_message(format_linht_pmt("EOT")), TxControlState.OFF)
        self.assertEqual(parse_tx_control_message("SOT"), TxControlState.ON)
        self.assertEqual(parse_tx_control_message("EOT"), TxControlState.OFF)


if __name__ == "__main__":
    unittest.main()
