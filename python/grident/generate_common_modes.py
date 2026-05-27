#!/usr/bin/env python3
"""Generate IQ test vectors for common gr-ident mode IDs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from grident.common_modes import COMMON_MODES, CommonMode
from grident.generate_test_iq import build_burst


def write_mode_capture(mode: CommonMode, output_dir: Path) -> tuple[Path, Path]:
    signal, meta = build_burst(mode.to_field())
    meta["name"] = mode.name
    meta["slug"] = mode.slug

    iq_path = output_dir / f"{mode.slug}.cf32"
    meta_path = output_dir / f"{mode.slug}.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    signal.tofile(iq_path)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return iq_path, meta_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("test_iq/vectors/common"),
        help="Directory for .cf32 and .json pairs",
    )
    args = parser.parse_args()

    manifest = []
    for mode in COMMON_MODES:
        iq_path, meta_path = write_mode_capture(mode, args.output_dir)
        manifest.append(
            {
                "mode_id": mode.mode_id,
                "name": mode.name,
                "digital": mode.digital,
                "iq": str(iq_path),
                "meta": str(meta_path),
            }
        )
        print(f"mode {mode.mode_id:3d} ({mode.name}): {iq_path}")

    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
