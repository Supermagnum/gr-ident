"""Modulation profile definition for gr-ident preamble air interfaces."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Callable, Literal

from ..iq_samples import IqSamples
from ..preamble import (
    PreambleField,
    bits_msb_first_to_codeword,
    codeword_to_bits_msb_first,
    decode_preamble,
    encode_preamble,
)
from . import fsk, psk, rtty

ModulationKind = Literal["cpfsk4", "bpsk", "fsk2"]

DEFAULT_SAMPLE_RATE = fsk.DEFAULT_SAMPLE_RATE
GUARD_SILENCE_SEC = 1.0


@dataclass(frozen=True)
class ModulationProfile:
    name: str
    description: str
    reference: str
    sample_rate: int
    sync_bits: tuple[int, ...]
    kind: ModulationKind = "cpfsk4"
    symbol_rate: float = fsk.SYMBOL_RATE
    deviations: tuple[float, float] = (648.0, 1944.0)
    overlay_builder: Callable[[int, int], list[float] | None] | None = None

    @property
    def sync_len(self) -> int:
        return len(self.sync_bits)

    @property
    def samples_per_symbol(self) -> int:
        if self.kind == "cpfsk4":
            return fsk.samples_per_symbol(self.sample_rate)
        if self.kind == "bpsk":
            return psk.samples_per_symbol(self.sample_rate)
        if self.kind == "fsk2":
            return rtty.samples_per_symbol(self.sample_rate)
        raise ValueError(f"unsupported modulation kind: {self.kind}")

    def _overlay(self, num_samples: int) -> list[float] | None:
        if self.overlay_builder is None:
            return None
        return self.overlay_builder(self.sample_rate, num_samples)

    def _modulate_bits(self, bits: list[int], *, apply_overlay: bool = True) -> IqSamples:
        if self.kind == "cpfsk4":
            overlay = None
            if apply_overlay and self.overlay_builder is not None:
                num_symbols = len(fsk.bits_to_symbols(bits))
                overlay = self._overlay(num_symbols * self.samples_per_symbol)
            return fsk.modulate_cpfsk(
                bits,
                self.deviations,
                sample_rate=self.sample_rate,
                frequency_overlay=overlay,
            )
        if self.kind == "bpsk":
            return psk.modulate_bpsk(bits, sample_rate=self.sample_rate)
        if self.kind == "fsk2":
            return rtty.modulate_fsk2(bits, sample_rate=self.sample_rate)
        raise ValueError(f"unsupported modulation kind: {self.kind}")

    def modulate_bits(self, bits: list[int]) -> IqSamples:
        return self._modulate_bits(bits)

    def _guard_silence_samples(self) -> int:
        return int(GUARD_SILENCE_SEC * self.sample_rate)

    def _silence(self, num_samples: int | None = None) -> list[complex]:
        count = num_samples if num_samples is not None else self._guard_silence_samples()
        return [0j] * count

    def modulate_preamble(self, field: PreambleField) -> tuple[IqSamples, dict]:
        codeword = encode_preamble(field)
        preamble_bits = codeword_to_bits_msb_first(codeword)
        bits = list(self.sync_bits) + preamble_bits
        burst = self._modulate_bits(bits, apply_overlay=False)
        tail_samples = 0
        if self.overlay_builder is not None:
            tail_samples = self.sample_rate // 10
            overlay = self._overlay(tail_samples)
            phase = float(cmath.phase(burst.data[-1])) if burst.data else 0.0
            tail: list[complex] = []
            for n in range(tail_samples):
                freq = overlay[n] if overlay else 0.0
                phase += 2.0 * math.pi * freq / self.sample_rate
                tail.append(cmath.exp(1j * phase))
            signal = IqSamples(burst.data + tail)
        else:
            signal = burst

        lead = self._silence()
        trail = self._silence()
        body = signal.data
        signal = IqSamples(lead + body + trail)

        meta = {
            "sample_rate": self.sample_rate,
            "center_freq": 0,
            "profile": self.name,
            "profile_reference": self.reference,
            "modulation": self.kind,
            "symbol_rate": self.symbol_rate,
            "mode_id": field.mode_id,
            "digital": field.digital,
            "encrypted": field.encrypted,
            "sync_bits": self.sync_len,
            "preamble_bits": 24,
            "guard_silence_sec": GUARD_SILENCE_SEC,
            "lead_silence_samples": len(lead),
            "trail_silence_samples": len(trail),
            "modulation_start": len(lead),
            "preamble_samples": burst.size,
            "modulated_samples": len(body),
            "expected_valid": True,
            "codeword_hex": f"0x{codeword:06x}",
        }
        if self.kind == "cpfsk4":
            meta["deviations_hz"] = list(self.deviations)
        if self.kind == "fsk2":
            meta["shift_hz"] = rtty.RTTY_MARK_HZ - rtty.RTTY_SPACE_HZ
            meta["mark_hz"] = rtty.RTTY_MARK_HZ
            meta["space_hz"] = rtty.RTTY_SPACE_HZ
        if self.overlay_builder is not None:
            meta["squelch_tail_samples"] = tail_samples
        meta["num_samples"] = signal.size
        meta["samples_per_symbol"] = self.samples_per_symbol
        return signal, meta

    def decode_signal(
        self, signal: IqSamples
    ) -> tuple[PreambleField | None, int, bool, int, int, int] | None:
        body_len = self._burst_sample_len()
        if self.overlay_builder is not None:
            body_len += self.sample_rate // 10
        search_len = min(
            len(signal),
            self._guard_silence_samples() + body_len + self.samples_per_symbol,
        )
        search = IqSamples(signal.data[:search_len])
        sync_start = self._correlate_sync(search)
        if sync_start is None:
            return None

        preamble_start = sync_start + self._sync_sample_len()
        bits = self._demodulate_preamble(signal, preamble_start)
        codeword = bits_msb_first_to_codeword(bits)
        try:
            field, errors, valid = decode_preamble(codeword)
        except ValueError:
            return None, -1, False, codeword, sync_start, preamble_start
        return field, errors, valid, codeword, sync_start, preamble_start

    def _burst_sample_len(self) -> int:
        if self.kind == "cpfsk4":
            return (len(fsk.bits_to_symbols(self.sync_bits)) + 12) * self.samples_per_symbol
        return (len(self.sync_bits) + 24) * self.samples_per_symbol

    def _sync_sample_len(self) -> int:
        if self.kind == "cpfsk4":
            return len(fsk.bits_to_symbols(self.sync_bits)) * self.samples_per_symbol
        return len(self.sync_bits) * self.samples_per_symbol

    def _correlate_sync(self, signal: IqSamples) -> int | None:
        sync = list(self.sync_bits)
        if self.kind == "cpfsk4":
            return fsk.correlate_sync(
                signal, sync, self.deviations, self.sample_rate
            )
        if self.kind == "bpsk":
            return psk.correlate_sync(signal, sync, self.sample_rate)
        if self.kind == "fsk2":
            return rtty.correlate_sync(signal, sync, self.sample_rate)
        raise ValueError(f"unsupported modulation kind: {self.kind}")

    def _demodulate_preamble(self, signal: IqSamples, start: int) -> list[int]:
        if self.kind == "cpfsk4":
            symbols = fsk.demodulate_cpfsk(
                signal,
                self.deviations,
                sample_rate=self.sample_rate,
                start=start,
                max_symbols=12,
            )
            return fsk.symbols_to_bits(symbols)[:24]
        if self.kind == "bpsk":
            return psk.demodulate_bpsk(
                signal,
                sample_rate=self.sample_rate,
                start=start,
                max_symbols=24,
            )[:24]
        if self.kind == "fsk2":
            return rtty.demodulate_fsk2(
                signal,
                sample_rate=self.sample_rate,
                start=start,
                max_symbols=24,
            )[:24]
        raise ValueError(f"unsupported modulation kind: {self.kind}")
