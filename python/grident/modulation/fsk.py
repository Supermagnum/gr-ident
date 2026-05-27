"""4-FSK CPFSK modulator and demodulator core."""

from __future__ import annotations

import cmath
import math
from typing import Iterable

from ..iq_samples import IqSamples, vdot

SYMBOL_RATE = 4800
DEFAULT_SAMPLE_RATE = 48000


def samples_per_symbol(sample_rate: int = DEFAULT_SAMPLE_RATE) -> int:
    if sample_rate % SYMBOL_RATE:
        raise ValueError("sample_rate must be an integer multiple of 4800")
    return sample_rate // SYMBOL_RATE


def bits_to_symbols(bits: Iterable[int]) -> list[int]:
    bit_list = [int(b) & 1 for b in bits]
    if len(bit_list) % 2:
        bit_list.append(0)
    return [(bit_list[i] << 1) | bit_list[i + 1] for i in range(0, len(bit_list), 2)]


def symbols_to_bits(symbols: Iterable[int]) -> list[int]:
    bits: list[int] = []
    for sym in symbols:
        bits.append((sym >> 1) & 1)
        bits.append(sym & 1)
    return bits


def symbol_frequency(symbol: int, deviations: tuple[float, float]) -> float:
    low, high = deviations
    table = (-high, -low, low, high)
    return table[symbol & 0x3]


def modulate_cpfsk(
    bits: Iterable[int],
    deviations: tuple[float, float],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    frequency_offset: float = 0.0,
    frequency_overlay: list[float] | None = None,
) -> IqSamples:
    """Continuous-phase 4-FSK at 4800 sym/s."""
    sps = samples_per_symbol(sample_rate)
    symbols = bits_to_symbols(bits)
    samples: list[complex] = []
    phase = 0.0
    sample_index = 0

    for symbol in symbols:
        freq = symbol_frequency(symbol, deviations) + frequency_offset
        for _ in range(sps):
            if frequency_overlay is not None:
                freq += frequency_overlay[sample_index]
            phase += 2.0 * math.pi * freq / sample_rate
            samples.append(cmath.exp(1j * phase))
            sample_index += 1

    return IqSamples(samples)


def demodulate_cpfsk_discriminator(
    signal: IqSamples | list[complex],
    deviations: tuple[float, float],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    start: int = 0,
    max_symbols: int | None = None,
    overlay: list[float] | None = None,
) -> list[int]:
    data = signal.data if isinstance(signal, IqSamples) else signal
    sps = samples_per_symbol(sample_rate)
    symbols: list[int] = []
    offset = start
    count = 0
    levels = [symbol_frequency(sym, deviations) for sym in range(4)]

    while offset + sps <= len(data):
        if max_symbols is not None and count >= max_symbols:
            break

        mean_freq = 0.0
        for i in range(1, sps):
            idx = offset + i
            dphase = cmath.phase(data[idx] * data[idx - 1].conjugate())
            freq = dphase * sample_rate / (2.0 * math.pi)
            if overlay is not None:
                freq -= overlay[idx]
            mean_freq += freq
        mean_freq /= max(1, sps - 1)

        best_sym = min(range(4), key=lambda sym: abs(mean_freq - levels[sym]))
        symbols.append(best_sym)
        offset += sps
        count += 1

    return symbols


def demodulate_cpfsk(
    signal: IqSamples | list[complex],
    deviations: tuple[float, float],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    start: int = 0,
    max_symbols: int | None = None,
    overlay: list[float] | None = None,
) -> list[int]:
    if overlay is not None:
        return demodulate_cpfsk_discriminator(
            signal, deviations, sample_rate, start, max_symbols, overlay
        )
    data = signal.data if isinstance(signal, IqSamples) else signal
    sps = samples_per_symbol(sample_rate)
    symbols: list[int] = []
    offset = start
    count = 0

    while offset + sps <= len(data):
        if max_symbols is not None and count >= max_symbols:
            break
        seg = data[offset : offset + sps]
        offset += sps

        best_sym = 0
        best_metric = -1.0
        for sym in range(4):
            freq = symbol_frequency(sym, deviations)
            ref = [
                cmath.exp(1j * 2.0 * math.pi * freq * (i / sample_rate))
                for i in range(sps)
            ]
            metric = abs(vdot(seg, ref))
            if metric > best_metric:
                best_metric = metric
                best_sym = sym
        symbols.append(best_sym)
        count += 1

    return symbols


def correlate_sync(
    signal: IqSamples,
    sync_bits: list[int],
    deviations: tuple[float, float],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    overlay: list[float] | None = None,
) -> int | None:
    expected = bits_to_symbols(sync_bits)
    nsync = len(expected)
    sps = samples_per_symbol(sample_rate)
    min_score = nsync
    best_idx = None

    search = len(signal) - nsync * sps
    for start in range(0, max(1, search + 1)):
        got = demodulate_cpfsk(
            signal,
            deviations,
            sample_rate=sample_rate,
            start=start,
            max_symbols=nsync,
            overlay=overlay,
        )
        if len(got) < nsync:
            continue
        score = sum(g != e for g, e in zip(got, expected))
        if score < min_score:
            min_score = score
            best_idx = start
            if score == 0:
                break

    return best_idx
