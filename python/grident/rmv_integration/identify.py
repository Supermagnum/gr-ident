"""Live receive-path signal identification (repeater runtime)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import numpy as np

from .backend import ClassifierBackend
from .runtime import IdentificationMode, RuntimeStatus

logger = logging.getLogger(__name__)


@dataclass
class IdentificationResult:
    """Result of identifying one received signal."""

    preamble_found: bool
    mode_id: int | None
    digital: bool | None
    encrypted: bool | None
    metadata_present: bool | None

    classifier_ran: bool
    classifier_backend: str
    predicted_family: str | None
    predicted_order: str | None
    family_confidence: float | None
    order_confidence: float | None

    preamble_classifier_agree: bool | None
    discrepancy_logged: bool

    routed_mode_id: int | None
    routing_source: str


async def identify_signal(
    iq_chunk: np.ndarray,
    runtime: RuntimeStatus,
    preamble_result: dict[str, object] | None,
) -> IdentificationResult:
    """
    Identify a received signal using the available backend.

    Preamble controls routing; classifier is advisory only.
    """
    if preamble_result is not None:
        mode_id = preamble_result.get("mode_id")
        digital = preamble_result.get("digital")
        encrypted = preamble_result.get("encrypted")
        metadata = preamble_result.get("metadata_present")
        routed_mode_id = int(mode_id) if mode_id is not None else None
        routing_source = "preamble"
        preamble_found = True
    else:
        mode_id = digital = encrypted = metadata = None
        routed_mode_id = None
        routing_source = "default"
        preamble_found = False

    classifier_ran = False
    predicted_family: str | None = None
    predicted_order: str | None = None
    family_confidence: float | None = None
    order_confidence: float | None = None
    agree: bool | None = None
    discrepancy_logged = False

    if runtime.identification_mode in (
        IdentificationMode.FULL,
        IdentificationMode.DEGRADED,
    ):
        try:
            result = await asyncio.wait_for(
                _run_classifier(iq_chunk, runtime),
                timeout=runtime.classifier_timeout_ms / 1000.0,
            )
            classifier_ran = True
            predicted_family = str(result.get("family", ""))
            predicted_order = str(result.get("order", ""))
            family_confidence = float(result.get("family_confidence", 0.0))
            order_confidence = float(result.get("order_confidence", 0.0))

            if preamble_found and mode_id is not None:
                from .mode_map import get_rmv_expectation

                expected = get_rmv_expectation(int(mode_id)) or {}
                exp_family = expected.get("family")
                agree = predicted_family == exp_family
                if not agree:
                    logger.warning(
                        "Preamble/classifier mismatch: preamble mode_id=%s "
                        "(%s) but classifier says %s (%.2f). Routing on preamble.",
                        mode_id,
                        exp_family,
                        predicted_family,
                        family_confidence or 0.0,
                    )
                    discrepancy_logged = True
            elif not preamble_found:
                routing_source = "classifier"

        except asyncio.TimeoutError:
            logger.warning(
                "Classifier timeout after %d ms - result discarded for this transmission",
                runtime.classifier_timeout_ms,
            )
        except Exception as exc:
            logger.error("Classifier error: %s", exc)

    return IdentificationResult(
        preamble_found=preamble_found,
        mode_id=int(mode_id) if mode_id is not None else None,
        digital=bool(digital) if digital is not None else None,
        encrypted=bool(encrypted) if encrypted is not None else None,
        metadata_present=bool(metadata) if metadata is not None else None,
        classifier_ran=classifier_ran,
        classifier_backend=runtime.classifier_backend.value,
        predicted_family=predicted_family,
        predicted_order=predicted_order,
        family_confidence=family_confidence,
        order_confidence=order_confidence,
        preamble_classifier_agree=agree,
        discrepancy_logged=discrepancy_logged,
        routed_mode_id=routed_mode_id,
        routing_source=routing_source,
    )


async def _run_classifier(iq_chunk: np.ndarray, runtime: RuntimeStatus) -> dict[str, object]:
    if runtime.classifier_backend == ClassifierBackend.NPU:
        return await _run_npu_classifier(iq_chunk)
    if runtime.classifier_backend == ClassifierBackend.CPU:
        return await _run_cpu_classifier(iq_chunk)
    return {}


async def _run_cpu_classifier(iq_chunk: np.ndarray) -> dict[str, object]:
    import json
    from pathlib import Path

    import onnxruntime as ort

    loop = asyncio.get_event_loop()

    def _infer() -> dict[str, object]:
        models_dir = Path(__file__).resolve().parents[3] / "models"
        sess_f = ort.InferenceSession(
            str(models_dir / "family_classifier.onnx"),
            providers=["CPUExecutionProvider"],
        )
        sess_o = ort.InferenceSession(
            str(models_dir / "order_classifier.onnx"),
            providers=["CPUExecutionProvider"],
        )
        meta_f = json.loads(sess_f.get_modelmeta().custom_metadata_map.get("class_names", "[]"))
        meta_o = json.loads(sess_o.get_modelmeta().custom_metadata_map.get("class_names", "[]"))

        x = iq_chunk[:1]
        f_logits = sess_f.run(None, {"iq_samples": x})[0]
        o_logits = sess_o.run(None, {"iq_samples": x})[0]

        def softmax(arr: np.ndarray) -> np.ndarray:
            e = np.exp(arr - arr.max())
            return e / e.sum()

        f_probs = softmax(f_logits[0])
        o_probs = softmax(o_logits[0])

        return {
            "family": meta_f[f_probs.argmax()] if meta_f else "",
            "order": meta_o[o_probs.argmax()] if meta_o else "",
            "family_confidence": float(f_probs.max()),
            "order_confidence": float(o_probs.max()),
        }

    return await loop.run_in_executor(None, _infer)


async def _run_npu_classifier(iq_chunk: np.ndarray) -> dict[str, object]:
    raise NotImplementedError(
        "NPU inference not yet implemented. "
        "Convert models with: spacemit-npu-convert family_classifier.onnx --output family.nb"
    )
