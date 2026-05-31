"""Markdown validation report generator."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .validator import ModeValidationResult, get_rmv_version, signal_passes


def _preamble_status(result: ModeValidationResult) -> str:
    p = result.preamble
    if p.decoded_ok and p.field_matches_fixture:
        return "pass"
    return "fail"


def _signal_status(result: ModeValidationResult) -> tuple[str, str, str]:
    s = result.signal
    if s is None:
        return "skip", "", ""
    if s.skipped:
        return "skip", "", s.skip_reason
    fam = f"{s.predicted_family} {'pass' if s.family_pass else 'fail'} ({s.family_confidence:.2f})"
    ord_ = f"{s.predicted_order} {'pass' if s.order_pass else 'fail'} ({s.order_confidence:.2f})"
    if s.known_ambiguity and not s.order_pass:
        ord_ += " (known ambiguity)"
    return "pass" if signal_passes(s) else "fail", fam, ord_


def generate_report(
    results: list[ModeValidationResult],
    *,
    rmv_version: str | None = None,
) -> str:
    """Build markdown report text from validation results."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rmv_ver = rmv_version or get_rmv_version()

    pre_checked = len(results)
    pre_passed = sum(
        1 for r in results if r.preamble.decoded_ok and r.preamble.field_matches_fixture
    )
    pre_failed = pre_checked - pre_passed - 0
    pre_skipped = sum(1 for r in results if "skipped" in r.preamble.notes.lower())

    sig_results = [r for r in results if r.signal is not None]
    sig_checked = len(sig_results)
    sig_passed = sum(1 for r in sig_results if signal_passes(r.signal))  # type: ignore[arg-type]
    sig_skipped = sum(1 for r in sig_results if r.signal and r.signal.skipped)
    sig_failed = sig_checked - sig_passed - sig_skipped

    lines = [
        "# gr-ident Validation Report",
        "",
        f"Generated: {ts}",
        f"radio-modulation-validator: {rmv_ver}",
        "",
        "## Summary",
        "",
        "| Layer | Checked | Passed | Failed | Skipped |",
        "|---|---|---|---|---|",
        f"| Preamble (Golay roundtrip) | {pre_checked} | {pre_passed} | {pre_failed} | {pre_skipped} |",
        f"| Signal (rmv classifier) | {sig_checked} | {sig_passed} | {sig_failed} | {sig_skipped} |",
        "",
        "## Per-mode results",
        "",
        "| Mode ID | Name | Preamble | Signal family | Signal order | Notes |",
        "|---|---|---|---|---|---|",
    ]

    for r in results:
        pre = "pass" if _preamble_status(r) == "pass" else "fail"
        sig_stat, fam, ord_ = _signal_status(r)
        notes = r.preamble.notes
        if r.signal and r.signal.notes:
            notes = (notes + "; " + r.signal.notes).strip("; ")
        if r.signal and r.signal.skipped:
            notes = r.signal.skip_reason
        lines.append(
            f"| {r.mode_id} | {r.mode_name} | {pre} | {fam} | {ord_} | {notes} |"
        )

    ambiguities = [
        (r.mode_id, r.signal.known_ambiguity)
        for r in results
        if r.signal and r.signal.known_ambiguity and not signal_passes(r.signal)
    ]
    lines.extend(["", "## Known ambiguities", ""])
    if ambiguities:
        for mode_id, text in ambiguities:
            lines.append(f"- Mode {mode_id}: {text}")
    else:
        lines.append("(none triggered in this run)")

    lines.extend(
        [
            "",
            "## Methodology",
            "",
            "Preamble validation: Golay(24,12) encode, decode roundtrip, field",
            "extraction, and comparison against committed fixture codewords.",
            "",
            "Signal validation: IQ test vectors classified by radio-modulation-validator",
            "family and order classifiers (ONNX, 91.84% family accuracy, 70.48% order",
            "accuracy on 43 classes). Reference data generated independently from",
            "gr-ident blocks.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    results: list[ModeValidationResult],
    path: Path,
    *,
    rmv_version: str | None = None,
) -> None:
    """Write markdown report to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_report(results, rmv_version=rmv_version), encoding="utf-8")
