#!/usr/bin/env python3
"""Decode gr-ident preamble from a generated reference IQ capture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from grident.iq_decode import decode_iq_file, load_iq_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--meta", type=Path, default=None)
    parser.add_argument("--expect-mode-id", type=int, default=None)
    args = parser.parse_args()

    meta_path = args.meta or args.input.with_suffix(".json")
    meta = load_iq_metadata(args.input) if meta_path.exists() else {}
    if args.meta and args.meta.exists():
        meta = load_iq_metadata(args.input)

    result = decode_iq_file(args.input)
    if result is None:
        print("Sync not found", file=sys.stderr)
        return 1

    print(f"sync_start={result.sync_start} preamble_start={result.preamble_start}")
    print(f"codeword=0x{result.codeword:06x} valid={result.valid} errors={result.golay_errors}")
    print(
        f"mode_id={result.mode_id} digital={result.digital} encrypted={result.encrypted}"
    )

    expected = args.expect_mode_id
    if expected is None and "mode_id" in meta:
        expected = meta["mode_id"]

    if not result.valid:
        return 2
    if expected is not None and result.mode_id != expected:
        print(f"Expected mode_id {expected}, got {result.mode_id}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
    raise SystemExit(main())
