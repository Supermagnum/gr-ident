"""Legacy shim — use grident.modulation instead."""

from __future__ import annotations

from .modulation.fsk import (
    DEFAULT_SAMPLE_RATE as SAMPLE_RATE,
    bits_to_symbols,
    demodulate_cpfsk as demodulate_4fsk,
    modulate_cpfsk as modulate_4fsk,
    samples_per_symbol,
    symbols_to_bits,
)
from .modulation.registry import NFM_125_4800

REFERENCE_SYNC_BITS = list(NFM_125_4800.sync_bits)

__all__ = [
    "REFERENCE_SYNC_BITS",
    "SAMPLE_RATE",
    "bits_to_symbols",
    "demodulate_4fsk",
    "modulate_4fsk",
    "samples_per_symbol",
    "symbols_to_bits",
]
