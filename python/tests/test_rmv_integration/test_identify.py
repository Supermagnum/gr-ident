"""Tests for live receive-path identification."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))

from grident.rmv_integration.backend import ClassifierBackend
from grident.rmv_integration.identify import identify_signal
from grident.rmv_integration.runtime import IdentificationMode, RuntimeStatus


def _runtime(mode: IdentificationMode, backend: ClassifierBackend) -> RuntimeStatus:
    return RuntimeStatus(
        identification_mode=mode,
        classifier_backend=backend,
        gr_ident_available=True,
        rmv_available=True,
        classifier_timeout_ms=500,
        notes="test",
    )


class IdentifyTests(unittest.IsolatedAsyncioTestCase):
    async def test_preamble_routes_immediately(self) -> None:
        runtime = _runtime(IdentificationMode.MINIMAL, ClassifierBackend.NONE)
        preamble = {"mode_id": 100, "digital": True, "encrypted": False, "metadata_present": False}
        chunk = np.zeros((1, 2, 1024), dtype=np.float32)
        result = await identify_signal(chunk, runtime, preamble)
        self.assertEqual(result.routed_mode_id, 100)
        self.assertEqual(result.routing_source, "preamble")

    async def test_classifier_timeout_discarded(self) -> None:
        runtime = _runtime(IdentificationMode.DEGRADED, ClassifierBackend.CPU)

        async def slow_classifier(*_args, **_kwargs):
            await asyncio.sleep(2.0)
            return {"family": "FSK", "order": "DMR", "family_confidence": 0.9, "order_confidence": 0.9}

        with mock.patch(
            "grident.rmv_integration.identify._run_classifier",
            side_effect=slow_classifier,
        ):
            chunk = np.zeros((1, 2, 1024), dtype=np.float32)
            result = await identify_signal(chunk, runtime, None)
        self.assertFalse(result.classifier_ran)

    async def test_mismatch_logged_routes_on_preamble(self) -> None:
        runtime = _runtime(IdentificationMode.DEGRADED, ClassifierBackend.CPU)
        preamble = {"mode_id": 100, "digital": True, "encrypted": False, "metadata_present": False}

        async def fm_classifier(*_args, **_kwargs):
            return {
                "family": "FM",
                "order": "NBFM_25",
                "family_confidence": 0.95,
                "order_confidence": 0.90,
            }

        with mock.patch("grident.rmv_integration.identify._run_classifier", side_effect=fm_classifier):
            chunk = np.zeros((1, 2, 1024), dtype=np.float32)
            result = await identify_signal(chunk, runtime, preamble)

        self.assertEqual(result.routing_source, "preamble")
        self.assertTrue(result.discrepancy_logged)
        self.assertFalse(result.preamble_classifier_agree)

    async def test_no_preamble_classifier_runs(self) -> None:
        runtime = _runtime(IdentificationMode.DEGRADED, ClassifierBackend.CPU)

        async def fsk_classifier(*_args, **_kwargs):
            return {
                "family": "FSK",
                "order": "DMR",
                "family_confidence": 0.99,
                "order_confidence": 0.99,
            }

        with mock.patch("grident.rmv_integration.identify._run_classifier", side_effect=fsk_classifier):
            chunk = np.zeros((1, 2, 1024), dtype=np.float32)
            result = await identify_signal(chunk, runtime, None)

        self.assertTrue(result.classifier_ran)
        self.assertEqual(result.routing_source, "classifier")

    async def test_no_preamble_no_classifier(self) -> None:
        runtime = _runtime(IdentificationMode.MINIMAL, ClassifierBackend.NONE)
        chunk = np.zeros((1, 2, 1024), dtype=np.float32)
        result = await identify_signal(chunk, runtime, None)
        self.assertEqual(result.routing_source, "default")
        self.assertFalse(result.classifier_ran)

    def test_zmq_status_published(self) -> None:
        runtime = _runtime(IdentificationMode.DEGRADED, ClassifierBackend.CPU)
        status = runtime.to_zmq_status()
        expected_keys = {
            "classifier_backend",
            "gr_ident_available",
            "identification_mode",
            "rmv_available",
            "classifier_timeout_ms",
        }
        self.assertEqual(set(status.keys()), expected_keys)
        self.assertEqual(status["classifier_backend"], "cpu")
        self.assertEqual(status["identification_mode"], "degraded")


if __name__ == "__main__":
    unittest.main()
