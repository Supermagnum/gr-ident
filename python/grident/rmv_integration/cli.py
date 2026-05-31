"""CLI for grident-validate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import write_report
from .validator import (
    RMV_SKIP_MESSAGE,
    discover_fixture_mode_ids,
    find_rmv,
    print_rmv_missing_warning,
    rmv_importable,
    signal_passes,
    validate_mode,
)


def _default_fixtures() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "common_modes"


def _default_report() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "validation-report.md"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grident-validate",
        description="Two-layer gr-ident validation (preamble + rmv signal)",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=_default_fixtures(),
        help="path to fixture directory",
    )
    parser.add_argument(
        "--rmv",
        type=Path,
        default=None,
        help="path to rmv executable (auto-detected if not given)",
    )
    parser.add_argument("--mode", type=int, default=None, help="validate a single mode ID")
    parser.add_argument(
        "--report",
        type=Path,
        default=_default_report(),
        help="write markdown report to this path",
    )
    parser.add_argument(
        "--preamble-only",
        action="store_true",
        help="run preamble checks only, skip signal validation",
    )
    parser.add_argument(
        "--signal-only",
        action="store_true",
        help="run signal checks only, skip preamble validation",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="output format",
    )
    parser.add_argument("--verbose", action="store_true", help="show detailed per-mode output")
    parser.add_argument("--fail-fast", action="store_true", help="stop on first failure")
    return parser


def _print_table(results: list, *, preamble_only: bool = False) -> None:
    print(f"{'Mode':>6}  {'Name':<24}  {'Preamble':<8}  {'Signal':<8}  Notes")
    print("-" * 72)
    for r in results:
        pre = "PASS" if r.preamble.decoded_ok and r.preamble.field_matches_fixture else "FAIL"
        if preamble_only:
            sig = "SKIP"
            notes = "preamble-only"
        elif r.signal is None:
            sig = "SKIP"
            notes = "no IQ file"
        elif r.signal.skipped:
            sig = "SKIP"
            notes = r.signal.skip_reason
        elif signal_passes(r.signal):
            sig = "PASS"
            notes = ""
        else:
            sig = "FAIL"
            notes = r.signal.notes or "family/order mismatch"
        print(f"{r.mode_id:6d}  {r.mode_name:<24}  {pre:<8}  {sig:<8}  {notes}")


def _exit_code(results: list, *, signal_only: bool) -> int:
    if signal_only and find_rmv() is None and not rmv_importable():
        print(RMV_SKIP_MESSAGE, file=sys.stderr)
        return 2

    if not signal_only and not find_rmv() and not rmv_importable():
        print_rmv_missing_warning()

    for r in results:
        pre_ok = r.preamble.decoded_ok and r.preamble.field_matches_fixture
        if not pre_ok and "skipped" not in r.preamble.notes.lower():
            return 1
        if r.signal is not None and not signal_passes(r.signal, signal_required=signal_only):
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.preamble_only and args.signal_only:
        parser.error("cannot use --preamble-only and --signal-only together")

    fixture_dir = args.fixtures.resolve()
    if not fixture_dir.is_dir():
        print(f"Fixture directory not found: {fixture_dir}", file=sys.stderr)
        return 1

    if args.mode is not None:
        mode_ids = [args.mode]
    else:
        mode_ids = discover_fixture_mode_ids(fixture_dir)
        if not mode_ids:
            print(f"No mode_*.json fixtures in {fixture_dir}", file=sys.stderr)
            return 1

    results = []
    for mode_id in mode_ids:
        result = validate_mode(
            mode_id,
            fixture_dir,
            args.rmv,
            preamble_only=args.preamble_only,
            signal_only=args.signal_only,
        )
        results.append(result)

        if args.verbose and result.signal and not result.signal.skipped:
            s = result.signal
            print(
                f"  mode {mode_id}: family={s.predicted_family} ({s.family_confidence:.2f}) "
                f"order={s.predicted_order} ({s.order_confidence:.2f})",
                file=sys.stderr,
            )

        if args.fail_fast and not result.overall_pass:
            break

    if args.format == "json":
        payload = []
        for r in results:
            entry = {
                "mode_id": r.mode_id,
                "mode_name": r.mode_name,
                "overall_pass": r.overall_pass,
                "preamble": {
                    "decoded_ok": r.preamble.decoded_ok,
                    "field_matches_fixture": r.preamble.field_matches_fixture,
                    "codeword_hex": hex(r.preamble.encoded_codeword),
                    "notes": r.preamble.notes,
                },
            }
            if r.signal is not None:
                s = r.signal
                entry["signal"] = {
                    "skipped": s.skipped,
                    "skip_reason": s.skip_reason,
                    "expected_family": s.expected_family,
                    "expected_order": s.expected_order,
                    "predicted_family": s.predicted_family,
                    "predicted_order": s.predicted_order,
                    "family_pass": s.family_pass,
                    "order_pass": s.order_pass,
                    "notes": s.notes,
                }
            payload.append(entry)
        print(json.dumps(payload, indent=2))
    else:
        _print_table(results, preamble_only=args.preamble_only)

    if args.report:
        write_report(results, args.report.resolve())

    return _exit_code(results, signal_only=args.signal_only)


if __name__ == "__main__":
    raise SystemExit(main())
