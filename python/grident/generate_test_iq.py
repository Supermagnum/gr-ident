#!/usr/bin/env python3
"""Generate gr-ident IQ test vectors using modulation-specific air interfaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from grident.iq_samples import IqSamples, add_awgn
from grident.modulation.registry import get_profile, get_profile_for_mode
from grident.preamble import PreambleField


def build_burst(field: PreambleField, profile_name: str | None = None) -> tuple[IqSamples, dict]:
    profile = (
        get_profile(profile_name)
        if profile_name
        else get_profile_for_mode(field.mode_id)
    )
    return profile.modulate_preamble(field)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode-id", type=int, default=120)
    parser.add_argument("--profile", type=str, default=None, help="Override modulation profile name")
    parser.add_argument("--digital", action="store_true", default=True)
    parser.add_argument("--analog", action="store_true", help="Force analog flag")
    parser.add_argument("--encrypted", action="store_true")
    parser.add_argument("--snr", type=float, default=None, help="Add AWGN at SNR dB")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--meta", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    digital = not args.analog
    field = PreambleField(
        mode_id=args.mode_id,
        encrypted=args.encrypted,
        digital=digital,
    )
    signal, meta = build_burst(field, args.profile)
    if args.snr is not None:
        signal = IqSamples(add_awgn(signal.data, args.snr, args.seed))
        meta["snr_db"] = args.snr
        meta["seed"] = args.seed
        meta["num_samples"] = signal.size

    args.output.parent.mkdir(parents=True, exist_ok=True)
    signal.tofile(args.output)

    meta_path = args.meta or args.output.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({signal.size} samples) profile={meta['profile']}")
    print(f"Wrote {meta_path}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
