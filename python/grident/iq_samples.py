"""Complex float32 IQ sample I/O and helpers (stdlib only)."""

from __future__ import annotations

import array
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IqSamples:
    data: list[complex]

    @property
    def size(self) -> int:
        return len(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key: int | slice) -> complex | list[complex]:
        return self.data[key]

    def tofile(self, path: Path | str) -> None:
        write_cf32(path, self.data)

    @classmethod
    def fromfile(cls, path: Path | str) -> IqSamples:
        return cls(read_cf32(path))


def read_cf32(path: Path | str) -> list[complex]:
    raw = Path(path).read_bytes()
    if len(raw) % 8 != 0:
        raise ValueError("cf32 file size must be a multiple of 8 bytes")
    floats = array.array("f")
    floats.frombytes(raw)
    return [complex(floats[i], floats[i + 1]) for i in range(0, len(floats), 2)]


def write_cf32(path: Path | str, samples: list[complex]) -> None:
    floats = array.array("f")
    for sample in samples:
        floats.append(sample.real)
        floats.append(sample.imag)
    Path(path).write_bytes(floats.tobytes())


def signal_power(samples: list[complex]) -> float:
    if not samples:
        return 1.0
    return sum(abs(s) ** 2 for s in samples) / len(samples)


def add_awgn(samples: list[complex], snr_db: float, seed: int = 1) -> list[complex]:
    rng = random.Random(seed)
    power = signal_power(samples)
    noise_power = power / (10.0 ** (snr_db / 10.0))
    scale = math.sqrt(noise_power / 2.0)
    return [
        s + complex(rng.gauss(0.0, scale), rng.gauss(0.0, scale))
        for s in samples
    ]


def vdot(a: list[complex], b: list[complex]) -> complex:
    return sum(x * y.conjugate() for x, y in zip(a, b))
