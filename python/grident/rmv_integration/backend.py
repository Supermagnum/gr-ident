"""NPU/CPU classifier backend detection for repeater runtime."""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ClassifierBackend(Enum):
    NPU = "npu"
    CPU = "cpu"
    NONE = "none"


def detect_npu() -> bool:
    """Detect SpacemiT A100 NPU availability."""
    npu_paths = [
        Path("/sys/class/misc/spacemit-npu"),
        Path("/dev/spacemit-npu"),
        Path("/sys/bus/platform/drivers/spacemit-npu"),
    ]
    if not any(p.exists() for p in npu_paths):
        logger.info("NPU sysfs not found - NPU unavailable")
        return False

    try:
        import spacemit_npu  # type: ignore[import-untyped]

        _ = spacemit_npu.Runtime()
        logger.info("NPU runtime loaded successfully")
        return True
    except ImportError:
        logger.info("spacemit_npu SDK not installed - NPU unavailable")
        return False
    except Exception as exc:
        logger.warning("NPU runtime failed to initialise: %s", exc)
        return False


def detect_cpu_classifier(models_dir: Path) -> bool:
    """Detect ONNX CPU classifier availability."""
    family_model = models_dir / "family_classifier.onnx"
    order_model = models_dir / "order_classifier.onnx"

    if not family_model.exists() or not order_model.exists():
        logger.info("ONNX model files not found - CPU classifier unavailable")
        return False

    try:
        import numpy as np
        import onnxruntime as ort

        sess = ort.InferenceSession(
            str(family_model),
            providers=["CPUExecutionProvider"],
        )
        dummy = np.zeros((1, 2, 1024), dtype=np.float32)
        sess.run(None, {"iq_samples": dummy})
        logger.info("CPU classifier (ONNX) initialised successfully")
        return True
    except Exception as exc:
        logger.warning("CPU classifier failed to initialise: %s", exc)
        return False


def select_backend(models_dir: Path) -> ClassifierBackend:
    """Select the best available classifier backend (NPU > CPU > None)."""
    if detect_npu():
        return ClassifierBackend.NPU
    if detect_cpu_classifier(models_dir):
        return ClassifierBackend.CPU
    logger.warning(
        "No classifier backend available. Signal identification will use preamble only."
    )
    return ClassifierBackend.NONE
