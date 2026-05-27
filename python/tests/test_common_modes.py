"""Roundtrip and cross-identification tests for common mode IQ captures."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "python"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "common_modes"
sys.path.insert(0, str(PYTHON))

from grident.common_modes import COMMON_MODES, COMMON_MODE_BY_ID
from grident.generate_common_modes import write_mode_capture
from grident.iq_decode import decode_iq_file, load_iq_metadata


def ensure_fixtures(force: bool = False) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for mode in COMMON_MODES:
        iq_path = FIXTURES / f"{mode.slug}.cf32"
        if force or not iq_path.exists():
            write_mode_capture(mode, FIXTURES)


class CommonModeIqTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_fixtures(force=True)

    def test_fixture_manifest(self) -> None:
        for mode in COMMON_MODES:
            iq_path = FIXTURES / f"{mode.slug}.cf32"
            meta_path = FIXTURES / f"{mode.slug}.json"
            self.assertTrue(iq_path.exists(), msg=str(iq_path))
            self.assertTrue(meta_path.exists(), msg=str(meta_path))
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(meta["mode_id"], mode.mode_id)
            self.assertEqual(meta["digital"], mode.digital)
            self.assertEqual(meta["profile"], mode.profile_name)

    def test_real_modulation_profile_per_mode(self) -> None:
        expected = {
            20: "nfm_125_4800",
            30: "nfm_125_ctcss_4800",
            40: "nfm_125_dcs_4800",
            104: "c4fm_4800",
            108: "dpmr_4800",
            110: "nfm_125_4800",
            158: "psk31_3125",
            159: "rtty_50",
        }
        for mode in COMMON_MODES:
            self.assertEqual(mode.profile_name, expected[mode.mode_id])

    def test_wrong_profile_does_not_decode(self) -> None:
        from grident.iq_decode import decode_iq_signal
        from grident.iq_samples import IqSamples

        c4fm = FIXTURES / "mode_104.cf32"
        signal = IqSamples.fromfile(c4fm)
        wrong = decode_iq_signal(signal, "nfm_125_4800")
        self.assertTrue(wrong is None or not wrong.valid or wrong.mode_id != 104)

    def test_roundtrip_each_mode(self) -> None:
        for mode in COMMON_MODES:
            iq_path = FIXTURES / f"{mode.slug}.cf32"
            result = decode_iq_file(iq_path)
            self.assertIsNotNone(result, msg=f"sync failed for mode {mode.mode_id}")
            assert result is not None
            self.assertTrue(result.valid, msg=f"Golay failed for mode {mode.mode_id}")
            self.assertEqual(result.mode_id, mode.mode_id, msg=mode.name)
            self.assertEqual(result.digital, mode.digital, msg=mode.name)

    def test_cross_identification_matrix(self) -> None:
        decoded: dict[int, int] = {}
        codewords: dict[int, int] = {}

        for mode in COMMON_MODES:
            iq_path = FIXTURES / f"{mode.slug}.cf32"
            result = decode_iq_file(iq_path)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertTrue(result.valid)
            decoded[mode.mode_id] = result.mode_id
            codewords[mode.mode_id] = result.codeword

        self.assertEqual(len(decoded), len(COMMON_MODES))
        self.assertEqual(len(set(decoded.values())), len(COMMON_MODES))
        self.assertEqual(len(set(codewords.values())), len(COMMON_MODES))

        for source in COMMON_MODES:
            actual = decoded[source.mode_id]
            for expected in COMMON_MODES:
                if source.mode_id == expected.mode_id:
                    self.assertEqual(
                        actual,
                        expected.mode_id,
                        msg=f"{source.name} must identify as itself",
                    )
                else:
                    self.assertNotEqual(
                        actual,
                        expected.mode_id,
                        msg=(
                            f"{source.name} ({source.mode_id}) misidentified "
                            f"as {expected.name} ({expected.mode_id})"
                        ),
                    )

    def test_metadata_matches_decode(self) -> None:
        for mode in COMMON_MODES:
            iq_path = FIXTURES / f"{mode.slug}.cf32"
            meta = load_iq_metadata(iq_path)
            result = decode_iq_file(iq_path)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.mode_id, meta["mode_id"])
            self.assertEqual(result.digital, meta["digital"])
            self.assertEqual(result.profile, meta["profile"])

    def test_cli_rejects_wrong_expectation(self) -> None:
        mode = COMMON_MODES[0]
        iq_path = FIXTURES / f"{mode.slug}.cf32"
        wrong = next(m for m in COMMON_MODES if m.mode_id != mode.mode_id)

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "apps" / "grident_iq_test.py"),
                "--input",
                str(iq_path),
                "--expect-mode-id",
                str(wrong.mode_id),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_codewords_match_mode_table(self) -> None:
        for mode in COMMON_MODES:
            meta = json.loads((FIXTURES / f"{mode.slug}.json").read_text(encoding="utf-8"))
            self.assertIn(mode.mode_id, COMMON_MODE_BY_ID)
            self.assertEqual(meta["name"], COMMON_MODE_BY_ID[mode.mode_id].name)


if __name__ == "__main__":
    unittest.main()
