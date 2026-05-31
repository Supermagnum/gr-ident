"""Tests for mode_id to rmv mapping."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))

from grident.rmv_integration.mode_map import (
    EXCLUDED_FROM_SIGNAL_VALIDATION,
    MODE_TO_RMV,
    VALID_FAMILIES,
    get_rmv_expectation,
)


class ModeMapTests(unittest.TestCase):
    def test_all_mapped_modes_have_valid_family(self) -> None:
        for mode_id, mapping in MODE_TO_RMV.items():
            self.assertIn(mapping["family"], VALID_FAMILIES, msg=f"mode {mode_id}")

    def test_digital_modes_map_to_fsk_or_psk(self) -> None:
        for mode_id, mapping in MODE_TO_RMV.items():
            if mode_id >= 100 and mapping["family"] != "custom":
                self.assertIn(
                    mapping["family"],
                    {"FSK", "PSK", "QAM"},
                    msg=f"digital mode {mode_id} maps to {mapping['family']}",
                )

    def test_analog_modes_map_to_am_or_fm(self) -> None:
        for mode_id, mapping in MODE_TO_RMV.items():
            if mode_id < 100:
                self.assertIn(
                    mapping["family"],
                    {"AM", "FM"},
                    msg=f"analog mode {mode_id} maps to {mapping['family']}",
                )

    def test_sleipnir_maps_to_custom(self) -> None:
        self.assertEqual(MODE_TO_RMV[300]["family"], "custom")
        self.assertEqual(MODE_TO_RMV[300]["order"], "sleipnir_8qpsk")

    def test_no_excluded_mode_in_map(self) -> None:
        overlap = EXCLUDED_FROM_SIGNAL_VALIDATION & set(MODE_TO_RMV)
        self.assertEqual(overlap, set())

    def test_mode_21_aviation_override(self) -> None:
        nfm = get_rmv_expectation(21, {"profile": "nfm_833", "name": "NFM 8.33"})
        self.assertEqual(nfm["family"], "FM")
        am = get_rmv_expectation(
            21,
            {"profile": "am_air_833", "name": "Aviation AM", "modulation": "am_dsb"},
        )
        self.assertEqual(am["family"], "AM")
        self.assertEqual(am["order"], "AM_AIR_833")


if __name__ == "__main__":
    unittest.main()
