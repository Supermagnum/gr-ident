#!/usr/bin/env python3
"""Regenerate IQ vectors, run tests, and build docs with waterfall plots."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "python"
FIXTURES = ROOT / "python" / "tests" / "fixtures" / "common_modes"
TEST_IQ = ROOT / "test_iq" / "vectors" / "common"
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"

sys.path.insert(0, str(PYTHON))

from grident.common_modes import COMMON_MODES  # noqa: E402
from grident.docs_plots import (  # noqa: E402
    render_spectrum,
    render_time_plot,
    render_waterfall,
    render_waterfall_context,
)
from grident.generate_common_modes import write_mode_capture  # noqa: E402
from grident.iq_decode import decode_iq_file  # noqa: E402
from grident.iq_samples import IqSamples  # noqa: E402
from grident.modulation.registry import get_profile_for_mode  # noqa: E402


def regenerate_iq(output_dirs: list[Path]) -> list[dict]:
    manifest: list[dict] = []
    for output_dir in output_dirs:
        output_dir.mkdir(parents=True, exist_ok=True)

    for mode in COMMON_MODES:
        entry: dict = {
            "mode_id": mode.mode_id,
            "name": mode.name,
            "digital": mode.digital,
            "profile": mode.profile_name,
            "paths": {},
        }
        for output_dir in output_dirs:
            iq_path, meta_path = write_mode_capture(mode, output_dir)
            entry["paths"][str(output_dir.relative_to(ROOT))] = {
                "iq": str(iq_path.relative_to(ROOT)),
                "meta": str(meta_path.relative_to(ROOT)),
            }
        manifest.append(entry)
    return manifest


def run_tests() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "python/tests", "-v"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(PYTHON)},
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout + proc.stderr
    return proc.returncode, output


def decode_results(iq_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for mode in COMMON_MODES:
        iq_path = iq_dir / f"{mode.slug}.cf32"
        meta_path = iq_path.with_suffix(".json")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        profile = get_profile_for_mode(mode.mode_id)
        result = decode_iq_file(iq_path)
        sample_rate = int(meta.get("sample_rate", 48000))
        num_samples = int(meta.get("num_samples", 0))
        preamble_samples = int(meta.get("preamble_samples", 0))
        modulated_samples = int(meta.get("modulated_samples", preamble_samples))
        lead_samples = int(meta.get("lead_silence_samples", 0))
        trail_samples = int(meta.get("trail_silence_samples", 0))
        rows.append(
            {
                "mode_id": mode.mode_id,
                "name": mode.name,
                "profile": mode.profile_name,
                "modulation": profile.kind,
                "symbol_rate": profile.symbol_rate,
                "sample_rate": sample_rate,
                "samples": num_samples,
                "duration_sec": num_samples / sample_rate,
                "preamble_samples": preamble_samples,
                "preamble_duration_sec": preamble_samples / sample_rate,
                "modulated_samples": modulated_samples,
                "modulated_duration_sec": modulated_samples / sample_rate,
                "lead_silence_samples": lead_samples,
                "lead_silence_sec": lead_samples / sample_rate,
                "trail_silence_samples": trail_samples,
                "trail_silence_sec": trail_samples / sample_rate,
                "codeword_hex": meta.get("codeword_hex"),
                "decode_valid": bool(result and result.valid),
                "decode_mode_id": result.mode_id if result else None,
                "sync_start": result.sync_start if result else None,
                "roundtrip_ok": bool(
                    result
                    and result.valid
                    and result.mode_id == mode.mode_id
                    and result.digital == mode.digital
                ),
            }
        )
    return rows


def render_mode_images(iq_dir: Path, rows: list[dict]) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    for mode, row in zip(COMMON_MODES, rows):
        iq_path = iq_dir / f"{mode.slug}.cf32"
        signal = IqSamples.fromfile(iq_path)
        meta = {}
        meta_path = iq_path.with_suffix(".json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            sample_rate = int(meta["sample_rate"])

        slug = mode.slug
        render_waterfall(
            signal,
            IMAGES / f"{slug}_waterfall.png",
            sample_rate=sample_rate,
            floor_db=-55.0,
            ceil_db=5.0,
            meta=meta,
        )
        render_waterfall_context(
            signal,
            IMAGES / f"{slug}_waterfall_context.png",
            sample_rate=sample_rate,
            floor_db=-55.0,
            ceil_db=5.0,
        )
        render_time_plot(
            signal,
            IMAGES / f"{slug}_time.png",
            sample_rate=sample_rate,
            meta=meta,
        )
        render_spectrum(
            signal,
            IMAGES / f"{slug}_spectrum.png",
            sample_rate=sample_rate,
            floor_db=-55.0,
            ceil_db=5.0,
            meta=meta,
        )
        row["images"] = {
            "waterfall": f"images/{slug}_waterfall.png",
            "waterfall_context": f"images/{slug}_waterfall_context.png",
            "time": f"images/{slug}_time.png",
            "spectrum": f"images/{slug}_spectrum.png",
        }


def write_test_results(exit_code: int, test_output: str, rows: list[dict]) -> None:
    passed = exit_code == 0
    lines = [
        "# Test Results",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        f"**Overall:** {'PASS' if passed else 'FAIL'} (exit code {exit_code})",
        "",
        "## Unit Test Log",
        "",
        "```text",
        test_output.rstrip(),
        "```",
        "",
        "## Per-Mode IQ Roundtrip",
        "",
        "| Mode ID | Name | Profile | Modulation | Samples | Decode | Roundtrip |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in rows:
        decode = "OK" if row["decode_valid"] else "FAIL"
        roundtrip = "OK" if row["roundtrip_ok"] else "FAIL"
        lines.append(
            f"| {row['mode_id']} | {row['name']} | `{row['profile']}` | "
            f"{row['modulation']} @ {row['symbol_rate']} | {row['samples']} | "
            f"{decode} | {roundtrip} |"
        )

    lines.extend(
        [
            "",
            "## Codewords",
            "",
            "| Mode ID | Expected codeword | Sync start |",
            "|---:|---|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['mode_id']} | {row['codeword_hex']} | {row['sync_start']} |"
        )

    (DOCS / "test-results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_modulation_doc(rows: list[dict]) -> None:
    lines = [
        "# Modulation Test Captures",
        "",
        "Each mode uses a real air-interface profile. Waterfall plots are zoomed to the "
        f"modulated body (with guard-silence context) at **{14000 // 1000} kHz** wide "
        "(+/-7 kHz). Captures include **1 s guard silence** before and after the body.",
        "",
        "All IQ files are **48 kHz** complex float32 (`.cf32`). Total duration is "
        "`num_samples / 48000`. Structure: **1 s lead silence + 3 s modulated body + 1 s trail silence**.",
        "",
        "## Capture duration summary",
        "",
        "| Mode ID | Name | Total | Lead silence | Body | Trail silence | Preamble only |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['mode_id']} | {row['name']} | "
            f"{row['duration_sec']:.3f} s | {row['lead_silence_sec']:.3f} s | "
            f"{row['modulated_duration_sec']:.3f} s | {row['trail_silence_sec']:.3f} s | "
            f"{row['preamble_duration_sec']:.3f} s |"
        )
    lines.extend(
        [
            "",
        "The **body** is the 3 s modulated segment (preamble burst plus "
        "profile-specific payload). **Preamble only** is the sync + Golay burst "
        "without the payload extension.",
            "",
        ]
    )
    for mode, row in zip(COMMON_MODES, rows):
        profile = get_profile_for_mode(mode.mode_id)
        images = row.get("images", {})
        lines.extend(
            [
                f"## Mode {mode.mode_id} — {mode.name}",
                "",
                f"- **Profile:** `{mode.profile_name}`",
                f"- **Reference:** {profile.reference}",
                f"- **Modulation:** {profile.kind}, {profile.symbol_rate} baud/sym/s",
                f"- **Digital flag:** {mode.digital}",
                f"- **Total duration:** {row['duration_sec']:.3f} s ({row['samples']} samples)",
                f"- **Lead silence:** {row['lead_silence_sec']:.3f} s "
                f"({row['lead_silence_samples']} samples)",
                f"- **Modulated body:** {row['modulated_duration_sec']:.3f} s "
                f"({row['modulated_samples']} samples)",
                f"- **Trail silence:** {row['trail_silence_sec']:.3f} s "
                f"({row['trail_silence_samples']} samples)",
                f"- **Preamble burst only:** {row['preamble_duration_sec']:.3f} s "
                f"({row['preamble_samples']} samples)",
                f"- **Codeword:** {row['codeword_hex']}",
                "",
                "### Waterfall (14 kHz wide, zoomed to modulation)",
                "",
                f"![{mode.name} waterfall]({images.get('waterfall', '')})",
                "",
                "### Waterfall context (full capture)",
                "",
                f"![{mode.name} context]({images.get('waterfall_context', '')})",
                "",
                "### Time domain (magnitude)",
                "",
                f"![{mode.name} time]({images.get('time', '')})",
                "",
                "### Spectrum (14 kHz wide, averaged)",
                "",
                f"![{mode.name} spectrum]({images.get('spectrum', '')})",
                "",
            ]
        )
    (DOCS / "modulation-captures.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(rows: list[dict], passed: bool) -> None:
    mode_list = "\n".join(
        f"- Mode {m.mode_id}: {m.name} (`{m.profile_name}`)"
        for m in COMMON_MODES
    )
    text = f"""# gr-ident Documentation

Generated test documentation for gr-ident modulation profiles and IQ captures.

**Test status:** {'PASS' if passed else 'FAIL'}

## Contents

- [Modulation captures and waterfall plots](modulation-captures.md)
- [Test results](test-results.md)
- [Code chart](codechart.md)

## Tested modes

{mode_list}

## IQ vectors

Regenerated captures live in:

- `test_iq/vectors/common/` — development vectors
- `python/tests/fixtures/common_modes/` — regression fixtures

## Plot parameters

| Parameter | Value |
|---|---|
| Sample rate | 48000 Hz |
| Waterfall width | 14 kHz (+/-7 kHz) |
| Waterfall (detail) | Zoomed to modulated body; fine STFT for short bursts |
| Waterfall (context) | Full capture with 1 s guard silence each side |
| STFT (detail) | Adaptive: nfft 256-2048, hop 4-128 by body length |
| Image height | 480 px (time axis resampled) |
| Power range | -55 to +5 dB (relative) |

## Regenerate

```bash
PYTHONPATH=python python3 python/grident/generate_docs.py
```

Requires ImageMagick (`convert`) for PNG export.
"""
    (DOCS / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip unittest execution",
    )
    parser.add_argument(
        "--iq-only",
        action="store_true",
        help="Regenerate IQ files only",
    )
    args = parser.parse_args()

    print("Regenerating IQ captures...")
    manifest = regenerate_iq([TEST_IQ, FIXTURES])
    manifest_path = TEST_IQ / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")

    if args.iq_only:
        return 0

    print("Decoding captures...")
    rows = decode_results(TEST_IQ)

    print("Rendering plots (14 kHz waterfall)...")
    render_mode_images(TEST_IQ, rows)

    exit_code = 0
    test_output = "Tests skipped."
    if not args.skip_tests:
        print("Running unit tests...")
        exit_code, test_output = run_tests()

    DOCS.mkdir(parents=True, exist_ok=True)
    write_test_results(exit_code, test_output, rows)
    write_modulation_doc(rows)
    write_index(rows, exit_code == 0)

    print(f"Documentation written to {DOCS}/")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
