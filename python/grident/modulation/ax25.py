"""Bell 202 AFSK 1200 baud modulator/demodulator for AX.25-style preambles."""

from __future__ import annotations

import cmath
import math
from typing import Iterable

from ..iq_samples import IqSamples, vdot

AX25_BAUD = 1200
DEFAULT_SAMPLE_RATE = 48000

# Bell 202 tones relative to 1700 Hz center: mark 1200 Hz, space 2200 Hz.
AX25_MARK_HZ = -500.0
AX25_SPACE_HZ = 500.0


def samples_per_symbol(sample_rate: int = DEFAULT_SAMPLE_RATE) -> int:
    if sample_rate % AX25_BAUD:
        raise ValueError("sample_rate must be an integer multiple of 1200")
    return sample_rate // AX25_BAUD


def bit_frequency(bit: int) -> float:
    return AX25_MARK_HZ if int(bit) & 1 else AX25_SPACE_HZ


def modulate_fsk2(
    bits: Iterable[int],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> IqSamples:
    spb = samples_per_symbol(sample_rate)
    samples: list[complex] = []
    phase = 0.0
    for bit in bits:
        freq = bit_frequency(bit)
        for _ in range(spb):
            phase += 2.0 * math.pi * freq / sample_rate
            samples.append(cmath.exp(1j * phase))
    return IqSamples(samples)


def demodulate_fsk2(
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
    freqs = (AX25_SPACE_HZ, AX25_MARK_HZ)

    while offset + spb <= len(data):
        if max_symbols is not None and count >= max_symbols:
            break
        seg = data[offset : offset + spb]
        offset += spb
        best_bit = 0
        best_metric = -1.0
        for bit in (0, 1):
            freq = freqs[bit]
            ref = [
                cmath.exp(1j * 2.0 * math.pi * freq * (i / sample_rate))
                for i in range(spb)
            ]
            metric = abs(vdot(seg, ref))
            if metric > best_metric:
                best_metric = metric
                best_bit = bit
        bits.append(best_bit)
        count += 1
    return bits


def correlate_sync(
    signal: IqSamples,
    sync_bits: list[int],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> int | None:
    ref = modulate_fsk2(sync_bits, sample_rate=sample_rate).data
    ref_len = len(ref)
    if ref_len > len(signal):
        return None

    best_idx = None
    best_metric = -1.0
    spb = samples_per_symbol(sample_rate)
    search = len(signal) - ref_len

    for start in range(0, max(1, search + 1), spb):
        metric = abs(vdot(signal.data[start : start + ref_len], ref))
        if metric > best_metric:
            best_metric = metric
            best_idx = start

    if best_idx is None:
        return None

    refine_lo = max(0, best_idx - spb)
    refine_hi = min(search, best_idx + spb)
    for start in range(refine_lo, refine_hi + 1):
        metric = abs(vdot(signal.data[start : start + ref_len], ref))
        if metric > best_metric:
            best_metric = metric
            best_idx = start

    got = demodulate_fsk2(
        signal,
        sample_rate=sample_rate,
        start=best_idx,
        max_symbols=len(sync_bits),
    )
    if sum(g != e for g, e in zip(got, sync_bits)) == 0:
        return best_idx
    return best_idx if best_metric > 0 else None
