"""Tests for Golay preamble validation."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))

from grident.rmv_integration.preamble_check import (
    check_preamble_roundtrip,
    check_preamble_with_errors,
)

FIXTURES = ROOT / "python" / "tests" / "fixtures" / "common_modes"


class PreambleCheckTests(unittest.TestCase):
    def test_golay_roundtrip_mode_20(self) -> None:
        r = check_preamble_roundtrip(20, digital=False, encrypted=False, metadata_present=False)
        self.assertTrue(r.decoded_ok)
        self.assertEqual(r.encoded_codeword, 0xCB4014)

    def test_golay_roundtrip_mode_100(self) -> None:
        r = check_preamble_roundtrip(100, digital=True, encrypted=False, metadata_present=False)
        self.assertTrue(r.decoded_ok)
        self.assertEqual(r.encoded_codeword, 0x432864)

    def test_golay_roundtrip_mode_300(self) -> None:
        r = check_preamble_roundtrip(300, digital=True, encrypted=False, metadata_present=False)
        self.assertTrue(r.decoded_ok)
        self.assertEqual(r.encoded_codeword, 0x3E592C)

    def test_1_bit_error_corrected(self) -> None:
        r = check_preamble_with_errors(20, False, False, False, 1)
        self.assertTrue(r.decoded_ok)

    def test_2_bit_errors_corrected(self) -> None:
        r = check_preamble_with_errors(20, False, False, False, 2)
        self.assertTrue(r.decoded_ok)

    def test_3_bit_errors_corrected(self) -> None:
        r = check_preamble_with_errors(20, False, False, False, 3)
        self.assertTrue(r.decoded_ok)

    def test_4_bit_errors_fail(self) -> None:
        r = check_preamble_with_errors(20, False, False, False, 4)
        self.assertFalse(r.decoded_ok)

    def test_fixture_codeword_mode_020(self) -> None:
        meta = json.loads((FIXTURES / "mode_020.json").read_text(encoding="utf-8"))
        codeword = int(meta["codeword_hex"], 0)
        r = check_preamble_roundtrip(
            mode_id=20,
            digital=meta["digital"],
            encrypted=meta["encrypted"],
            metadata_present=meta.get("metadata_present", False),
            fixture_codeword=codeword,
        )
        self.assertTrue(r.field_matches_fixture)
        self.assertTrue(r.decoded_ok)


if __name__ == "__main__":
    unittest.main()
