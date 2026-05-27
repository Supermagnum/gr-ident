"""Python unit tests for grident."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "python"
sys.path.insert(0, str(PYTHON))

from grident.golay import decode_golay24, encode_golay24
from grident.iq_samples import IqSamples
from grident.preamble import PreambleField, decode_preamble, encode_preamble, pack_field, unpack_field


class GolayTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        for data in (0, 0xABC, 0x123, 0x7FF):
            codeword = encode_golay24(data)
            decoded, errors, valid = decode_golay24(codeword)
            self.assertTrue(valid)
            self.assertEqual(decoded, data)
            self.assertEqual(errors, 0)

    def test_single_bit_correction(self) -> None:
        codeword = encode_golay24(0x5A5) ^ (1 << 3)
        decoded, errors, valid = decode_golay24(codeword)
        self.assertTrue(valid)
        self.assertEqual(decoded, 0x5A5)
        self.assertEqual(errors, 1)


class PreambleTests(unittest.TestCase):
    def test_field_pack(self) -> None:
        raw = pack_field(PreambleField(mode_id=103, encrypted=True, digital=True))
        self.assertEqual(raw, 0x0C67)
        field = unpack_field(raw)
        self.assertEqual(field.mode_id, 103)
        self.assertTrue(field.encrypted)
        self.assertTrue(field.digital)

    def test_preamble_round_trip(self) -> None:
        field = PreambleField(mode_id=120, encrypted=False, digital=True)
        codeword = encode_preamble(field)
        decoded, errors, valid = decode_preamble(codeword)
        self.assertTrue(valid)
        assert decoded is not None
        self.assertEqual(decoded.mode_id, 120)
        self.assertEqual(errors, 0)


class MesonTests(unittest.TestCase):
    def test_meson_unit_tests(self) -> None:
        build = ROOT / "build"
        if not (build / "build.ninja").exists():
            self.skipTest("Meson build directory not configured")
        result = subprocess.run(
            ["meson", "test", "-C", str(build)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


class IqRoundtripTests(unittest.TestCase):
    def test_generated_iq(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            iq = Path(tmp) / "capture.cf32"
            gen = subprocess.run(
                [
                    sys.executable,
                    str(PYTHON / "grident" / "generate_test_iq.py"),
                    "--mode-id",
                    "110",
                    "--output",
                    str(iq),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(gen.returncode, 0, msg=gen.stderr)

            verify = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "apps" / "grident_iq_test.py"),
                    "--input",
                    str(iq),
                    "--expect-mode-id",
                    "110",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verify.returncode, 0, msg=verify.stdout + verify.stderr)

            meta = json.loads(iq.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(meta["mode_id"], 110)
            samples = IqSamples.fromfile(iq)
            self.assertGreater(samples.size, 0)


if __name__ == "__main__":
    unittest.main()
