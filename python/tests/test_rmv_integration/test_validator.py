"""Tests for rmv signal validation (mocked subprocess)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))

from grident.rmv_integration.validator import (
    SignalValidationResult,
    find_rmv,
    signal_passes,
    validate_iq_signal,
)

FIXTURES = ROOT / "python" / "tests" / "fixtures" / "common_modes"


class ValidatorTests(unittest.TestCase):
    def test_validate_without_rmv(self) -> None:
        iq = FIXTURES / "mode_020.cf32"
        if not iq.is_file():
            self.skipTest("mode_020.cf32 not present locally")
        with mock.patch("grident.rmv_integration.validator.find_rmv", return_value=None):
            with mock.patch("grident.rmv_integration.validator.rmv_importable", return_value=False):
                r = validate_iq_signal(20, iq)
        self.assertTrue(r.skipped)
        self.assertEqual(r.skip_reason, "radio-modulation-validator not found")
        self.assertFalse(r.rmv_available)

    def test_validate_excluded_mode(self) -> None:
        iq = FIXTURES / "mode_020.cf32"
        r = validate_iq_signal(511, iq)
        self.assertTrue(r.skipped)
        self.assertEqual(r.skip_reason, "Mode excluded from signal validation")

    def test_validate_unmapped_mode(self) -> None:
        iq = FIXTURES / "mode_020.cf32"
        r = validate_iq_signal(999, iq)
        self.assertTrue(r.skipped)
        self.assertIn("not in rmv mode map", r.skip_reason)

    def test_validate_parses_rmv_json(self) -> None:
        iq = FIXTURES / "mode_020.cf32"
        if not iq.is_file():
            self.skipTest("mode_020.cf32 not present locally")
        payload = {
            "predicted_family": "FM",
            "predicted_order": "NBFM_25",
            "family_confidence": 0.94,
            "order_confidence": 0.87,
            "family_pass": True,
            "order_pass": True,
        }
        proc = mock.Mock(returncode=0, stdout=json.dumps(payload), stderr="")

        with mock.patch("grident.rmv_integration.validator.find_rmv", return_value=Path("/bin/rmv")):
            with mock.patch("subprocess.run", return_value=proc):
                r = validate_iq_signal(20, iq, rmv_path=Path("/bin/rmv"))

        self.assertFalse(r.skipped)
        self.assertEqual(r.predicted_family, "FM")
        self.assertEqual(r.predicted_order, "NBFM_25")
        self.assertAlmostEqual(r.family_confidence, 0.94)
        self.assertTrue(r.family_pass)
        self.assertTrue(signal_passes(r))

    def test_validate_handles_rmv_error(self) -> None:
        iq = FIXTURES / "mode_020.cf32"
        if not iq.is_file():
            self.skipTest("mode_020.cf32 not present locally")
        proc = mock.Mock(returncode=1, stdout="not json at all", stderr="")

        with mock.patch("grident.rmv_integration.validator.find_rmv", return_value=Path("/bin/rmv")):
            with mock.patch("subprocess.run", return_value=proc):
                r = validate_iq_signal(20, iq, rmv_path=Path("/bin/rmv"))

        self.assertFalse(r.skipped)
        self.assertFalse(r.family_pass)
        self.assertIn("no JSON", r.notes)


if __name__ == "__main__":
    unittest.main()
