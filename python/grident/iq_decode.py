"""Decode gr-ident preamble from modulation-specific IQ captures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .iq_samples import IqSamples
from .modulation.registry import get_profile, get_profile_for_mode
from .preamble import PreambleField


@dataclass
class IqDecodeResult:
    mode_id: int
    digital: bool
    encrypted: bool
    codeword: int
    golay_errors: int
    valid: bool
    sync_start: int
    preamble_start: int
    profile: str


def decode_iq_signal(
    signal: IqSamples,
    profile_name: str,
) -> IqDecodeResult | None:
    profile = get_profile(profile_name)
    decoded = profile.decode_signal(signal)
    if decoded is None:
        return None

    field, errors, valid, codeword, sync_start, preamble_start = decoded
    if field is None:
        return IqDecodeResult(
            mode_id=0,
            digital=False,
            encrypted=False,
            codeword=codeword,
            golay_errors=errors,
            valid=False,
            sync_start=sync_start,
            preamble_start=preamble_start,
            profile=profile.name,
        )

    return IqDecodeResult(
        mode_id=field.mode_id,
        digital=field.digital,
        encrypted=field.encrypted,
        codeword=codeword,
        golay_errors=errors,
        valid=valid,
        sync_start=sync_start,
        preamble_start=preamble_start,
        profile=profile.name,
    )


def decode_iq_file(path: Path, profile_name: str | None = None) -> IqDecodeResult | None:
    meta = load_iq_metadata(path)
    if profile_name is None:
        if "profile" in meta:
            profile_name = meta["profile"]
        elif "mode_id" in meta:
            profile_name = get_profile_for_mode(meta["mode_id"]).name
        else:
            raise ValueError(f"cannot determine profile for {path}")

    return decode_iq_signal(IqSamples.fromfile(path), profile_name)


def load_iq_metadata(path: Path) -> dict:
    meta_path = path.with_suffix(".json")
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def field_from_result(result: IqDecodeResult) -> PreambleField:
    return PreambleField(
        mode_id=result.mode_id,
        encrypted=result.encrypted,
        digital=result.digital,
    )
