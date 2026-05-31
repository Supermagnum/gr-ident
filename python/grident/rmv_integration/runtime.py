"""Runtime identification mode selection for repeater integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .backend import ClassifierBackend, select_backend

TIMEOUT_THRESHOLD = 3
TIMEOUT_WINDOW_SEC = 60


class IdentificationMode(Enum):
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"
    FALLBACK = "fallback"


@dataclass
class RuntimeStatus:
    identification_mode: IdentificationMode
    classifier_backend: ClassifierBackend
    gr_ident_available: bool
    rmv_available: bool
    classifier_timeout_ms: int
    notes: str

    def to_zmq_status(self) -> dict[str, object]:
        """Publish on ZeroMQ status socket (SDR-repeater telemetry plane)."""
        return {
            "classifier_backend": self.classifier_backend.value,
            "gr_ident_available": self.gr_ident_available,
            "identification_mode": self.identification_mode.value,
            "rmv_available": self.rmv_available,
            "classifier_timeout_ms": self.classifier_timeout_ms,
        }


class ClassifierTimeoutTracker:
    """Disable CPU classifier after repeated timeouts within a rolling window."""

    def __init__(
        self,
        threshold: int = TIMEOUT_THRESHOLD,
        window_sec: float = TIMEOUT_WINDOW_SEC,
    ) -> None:
        self.threshold = threshold
        self.window_sec = window_sec
        self._timestamps: list[float] = []

    def record_timeout(self, now: float) -> bool:
        """Record a timeout; return True if threshold exceeded."""
        self._timestamps = [t for t in self._timestamps if now - t <= self.window_sec]
        self._timestamps.append(now)
        return len(self._timestamps) >= self.threshold

    def reset(self) -> None:
        self._timestamps.clear()


def initialise_runtime(
    models_dir: Path,
    classifier_timeout_ms: int = 500,
) -> RuntimeStatus:
    """Detect available backends and return runtime status."""
    from .validator import find_rmv, rmv_importable

    backend = select_backend(models_dir)
    rmv = find_rmv() is not None or rmv_importable()

    if backend == ClassifierBackend.NPU:
        mode = IdentificationMode.FULL
    elif backend == ClassifierBackend.CPU:
        mode = IdentificationMode.DEGRADED
    else:
        mode = IdentificationMode.MINIMAL

    notes_map = {
        IdentificationMode.FULL: "Full two-layer identification: preamble + NPU classifier",
        IdentificationMode.DEGRADED: "Degraded: preamble + CPU classifier (~100-300ms latency)",
        IdentificationMode.MINIMAL: "Minimal: preamble routing only, no signal classifier",
        IdentificationMode.FALLBACK: "Fallback: no preamble, no classifier - default mode policy",
    }

    return RuntimeStatus(
        identification_mode=mode,
        classifier_backend=backend,
        gr_ident_available=True,
        rmv_available=rmv,
        classifier_timeout_ms=classifier_timeout_ms,
        notes=notes_map[mode],
    )


def apply_timeout_fallback(
    runtime: RuntimeStatus,
    tracker: ClassifierTimeoutTracker,
    now: float,
) -> bool:
    """
    If timeout threshold exceeded, downgrade runtime to MINIMAL.
    Returns True when mode changed.
    """
    if runtime.identification_mode not in (
        IdentificationMode.FULL,
        IdentificationMode.DEGRADED,
    ):
        return False
    if not tracker.record_timeout(now):
        return False
    runtime.identification_mode = IdentificationMode.MINIMAL
    runtime.classifier_backend = ClassifierBackend.NONE
    runtime.notes = "Classifier disabled due to repeated timeouts"
    return True
