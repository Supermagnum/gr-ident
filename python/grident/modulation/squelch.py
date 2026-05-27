"""CTCSS and DCS overlay for NFM profiles."""

from __future__ import annotations

import math

CTCSS_RATE = 88.5
CTCSS_DEVIATION_HZ = 500.0

DCS_RATE = 134.4
DCS_SHIFT_HZ = 134.0

DCS_CODE_023_BITS = (
    1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0,
)


def ctcss_overlay(sample_rate: int, num_samples: int, tone_hz: float = CTCSS_RATE) -> list[float]:
    return [
        CTCSS_DEVIATION_HZ * math.sin(2.0 * math.pi * tone_hz * n / sample_rate)
        for n in range(num_samples)
    ]


def dcs_overlay(sample_rate: int, num_samples: int, code: int = 0x0471) -> list[float]:
    del code
    bit_len = sample_rate / DCS_RATE
    return [
        DCS_SHIFT_HZ if DCS_CODE_023_BITS[int(n / bit_len) % len(DCS_CODE_023_BITS)] else -DCS_SHIFT_HZ
        for n in range(num_samples)
    ]
