"""BPSK modulator and demodulator for PSK31-style preambles."""

from __future__ import annotations

import cmath
import math
from typing import Iterable

from ..iq_samples import IqSamples, vdot

PSK31_BAUD = 31.25
DEFAULT_SAMPLE_RATE = 48000


def samples_per_symbol(sample_rate: int = DEFAULT_SAMPLE_RATE) -> int:
    sps = sample_rate / PSK31_BAUD
    if abs(sps - round(sps)) > 1e-9:
        raise ValueError("sample_rate must be an integer multiple of 31.25 Hz")
    return int(round(sps))


def modulate_bpsk(
    bits: Iterable[int],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> IqSamples:
    """NRZ BPSK at 31.25 baud (PSK31 symbol rate)."""
    spb = samples_per_symbol(sample_rate)
    samples: list[complex] = []
    for bit in bits:
        phase = math.pi if int(bit) & 1 else 0.0
        symbol = cmath.exp(1j * phase)
        samples.extend([symbol] * spb)
    return IqSamples(samples)


def demodulate_bpsk(
    signal: IqSamples | list[complex],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    start: int = 0,
    max_symbols: int | None = None,
) -> list[int]:
    data = signal.data if isinstance(signal, IqSamples) else signal
    spb = samples_per_symbol(sample_rate)
    bits: list[int] = []
    offset = start
    count = 0

    while offset + spb <= len(data):
        if max_symbols is not None and count >= max_symbols:
            break
        seg = data[offset : offset + spb]
        offset += spb

        ref0 = [1.0 + 0.0j] * spb
        ref1 = [cmath.exp(1j * math.pi)] * spb
        metric0 = vdot(seg, ref0).real
        metric1 = vdot(seg, ref1).real
        bits.append(1 if metric1 > metric0 else 0)
        count += 1

    return bits


def correlate_sync(
    signal: IqSamples,
    sync_bits: list[int],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> int | None:
    ref = modulate_bpsk(sync_bits, sample_rate=sample_rate).data
    ref_len = len(ref)
    if ref_len > len(signal):
        return None

    best_idx = None
    best_metric = -1.0
    spb = samples_per_symbol(sample_rate)
    search = len(signal) - ref_len

    for start in range(0, max(1, search + 1), spb):
        metric = vdot(signal.data[start : start + ref_len], ref).real
        if metric > best_metric:
            best_metric = metric
            best_idx = start

    if best_idx is None:
        return None

    refine_lo = max(0, best_idx - spb)
    refine_hi = min(search, best_idx + spb)
    for start in range(refine_lo, refine_hi + 1):
        metric = vdot(signal.data[start : start + ref_len], ref).real
        if metric > best_metric:
            best_metric = metric
            best_idx = start

    got = demodulate_bpsk(
        signal,
        sample_rate=sample_rate,
        start=best_idx,
        max_symbols=len(sync_bits),
    )
    if sum(g != e for g, e in zip(got, sync_bits)) == 0:
        return best_idx
    return best_idx if best_metric > 0 else None
