"""Tests for classifier backend detection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))

from grident.rmv_integration.backend import (
    ClassifierBackend,
    detect_cpu_classifier,
    detect_npu,
    select_backend,
)


class BackendTests(unittest.TestCase):
    def test_detect_npu_no_sysfs(self) -> None:
        with mock.patch("pathlib.Path.exists", return_value=False):
            self.assertFalse(detect_npu())

    def test_detect_npu_sdk_missing(self) -> None:
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch(
                "builtins.__import__",
                side_effect=ImportError("no sdk"),
            ):
                self.assertFalse(detect_npu())

    def test_detect_cpu_missing_models(self) -> None:
        empty = Path("/nonexistent/models")
        self.assertFalse(detect_cpu_classifier(empty))

    def test_detect_cpu_bad_onnx(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp)
            (models / "family_classifier.onnx").write_bytes(b"not onnx")
            (models / "order_classifier.onnx").write_bytes(b"not onnx")
            self.assertFalse(detect_cpu_classifier(models))

    def test_select_backend_prefers_npu(self) -> None:
        with mock.patch("grident.rmv_integration.backend.detect_npu", return_value=True):
            with mock.patch("grident.rmv_integration.backend.detect_cpu_classifier", return_value=True):
                self.assertEqual(select_backend(Path("/tmp")), ClassifierBackend.NPU)

    def test_select_backend_falls_back_to_cpu(self) -> None:
        with mock.patch("grident.rmv_integration.backend.detect_npu", return_value=False):
            with mock.patch("grident.rmv_integration.backend.detect_cpu_classifier", return_value=True):
                self.assertEqual(select_backend(Path("/tmp")), ClassifierBackend.CPU)

    def test_select_backend_none(self) -> None:
        with mock.patch("grident.rmv_integration.backend.detect_npu", return_value=False):
            with mock.patch("grident.rmv_integration.backend.detect_cpu_classifier", return_value=False):
                self.assertEqual(select_backend(Path("/tmp")), ClassifierBackend.NONE)


if __name__ == "__main__":
    unittest.main()
