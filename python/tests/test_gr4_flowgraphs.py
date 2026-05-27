"""GR4 flowgraph runner and PTT/ZMQ smoke tests."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD_GR4 = ROOT / "build-gr4"
FIXTURE = ROOT / "python/tests/fixtures/common_modes/mode_110.cf32"


def _binary(name: str) -> Path | None:
    path = BUILD_GR4 / name
    return path if path.is_file() else None


@unittest.skipUnless(_binary("grident_receive_flowgraph"), "build-gr4/grident_receive_flowgraph not found")
class Gr4ReceiveFlowgraphTest(unittest.TestCase):
    def test_mode_110_fixture(self) -> None:
        exe = _binary("grident_receive_flowgraph")
        assert exe is not None
        proc = subprocess.run(
            [str(exe), str(FIXTURE), "110"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("OK mode_id=110", proc.stdout)


@unittest.skipUnless(_binary("grident_ptt_zmq_smoke"), "build-gr4/grident_ptt_zmq_smoke not found")
class Gr4PttZmqSmokeTest(unittest.TestCase):
    def test_ptt_preamble_burst(self) -> None:
        exe = _binary("grident_ptt_zmq_smoke")
        assert exe is not None
        proc = subprocess.run(
            [str(exe)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("PTT/ZMQ smoke test OK", proc.stdout)
        self.assertIn("codeword=0x", proc.stdout)
        self.assertIn("profile=grident", proc.stdout)
        self.assertIn("profile=linht", proc.stdout)


@unittest.skip("YAML loader requires scheduler-wrapped graph; use grident_receive_flowgraph")
class Gr4YamlFlowgraphTest(unittest.TestCase):
    def test_receive_yaml(self) -> None:
        exe = _binary("grident_run_flowgraph")
        yaml_path = ROOT / "apps/flowgraphs/receive_iq_detect.gr.yaml"
        assert exe is not None
        proc = subprocess.run(
            [
                str(exe),
                str(yaml_path),
                f"REPLACE_ME.cf32={FIXTURE}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("Flowgraph finished", proc.stdout)


if __name__ == "__main__":
    unittest.main()
