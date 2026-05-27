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
from ..metadata_field import MetadataField, decode_metadata, encode_metadata
from . import ax25, fsk, psk, rtty

ModulationKind = Literal["cpfsk4", "bpsk", "fsk2"]

DEFAULT_SAMPLE_RATE = fsk.DEFAULT_SAMPLE_RATE
GUARD_SILENCE_SEC = 1.0
MODULATED_BODY_SEC = 3.0


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
            return self._fsk2_backend().samples_per_symbol(self.sample_rate)
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

    def _body_sample_target(self) -> int:
        return int(MODULATED_BODY_SEC * self.sample_rate)

    def _extend_body(self, burst: IqSamples) -> tuple[list[complex], int]:
        """Pad or trim the burst to MODULATED_BODY_SEC of modulated samples."""
        target = self._body_sample_target()
        if burst.size >= target:
            return burst.data[:target], 0

        extend = target - burst.size
        phase = float(cmath.phase(burst.data[-1])) if burst.data else 0.0
        out = list(burst.data)

        if self.overlay_builder is not None:
            overlay = self._overlay(extend)
            for n in range(extend):
                freq = overlay[n] if overlay else 0.0
                phase += 2.0 * math.pi * freq / self.sample_rate
                out.append(cmath.exp(1j * phase))
            return out, extend

        if self.kind == "fsk2":
            backend = self._fsk2_backend()
            mark = backend.AX25_MARK_HZ if backend is ax25 else rtty.RTTY_MARK_HZ
            for _ in range(extend):
                phase += 2.0 * math.pi * mark / self.sample_rate
                out.append(cmath.exp(1j * phase))
            return out, extend

        for _ in range(extend):
            out.append(cmath.exp(1j * phase))
        return out, extend

    def _fsk2_backend(self):
        if self.symbol_rate == ax25.AX25_BAUD:
            return ax25
        return rtty

    def _preamble_bit_count(self, field: PreambleField) -> int:
        return 48 if field.metadata_present else 24

    def modulate_preamble(
        self,
        field: PreambleField,
        metadata: MetadataField | None = None,
    ) -> tuple[IqSamples, dict]:
        if metadata is not None and not field.metadata_present:
            field = PreambleField(
                mode_id=field.mode_id,
                encrypted=field.encrypted,
                digital=field.digital,
                metadata_present=True,
            )
        codeword = encode_preamble(field)
        preamble_bits = codeword_to_bits_msb_first(codeword)
        metadata_codeword = None
        if field.metadata_present:
            meta_field = metadata if metadata is not None else MetadataField()
            metadata_codeword = encode_metadata(meta_field)
            preamble_bits.extend(codeword_to_bits_msb_first(metadata_codeword))
        bits = list(self.sync_bits) + preamble_bits
        burst = self._modulate_bits(bits, apply_overlay=False)
        body, payload_samples = self._extend_body(burst)

        lead = self._silence()
        trail = self._silence()
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
            "preamble_bits": len(preamble_bits),
            "metadata_present": field.metadata_present,
            "guard_silence_sec": GUARD_SILENCE_SEC,
            "modulated_body_sec": MODULATED_BODY_SEC,
            "lead_silence_samples": len(lead),
            "trail_silence_samples": len(trail),
            "modulation_start": len(lead),
            "preamble_samples": burst.size,
            "payload_samples": payload_samples,
            "modulated_samples": len(body),
            "expected_valid": True,
            "codeword_hex": f"0x{codeword:06x}",
        }
        if metadata_codeword is not None:
            meta["metadata_codeword_hex"] = f"0x{metadata_codeword:06x}"
        if self.kind == "cpfsk4":
            meta["deviations_hz"] = list(self.deviations)
        if self.kind == "fsk2":
            backend = self._fsk2_backend()
            meta["shift_hz"] = backend.AX25_MARK_HZ - backend.AX25_SPACE_HZ if backend is ax25 else rtty.RTTY_MARK_HZ - rtty.RTTY_SPACE_HZ
            meta["mark_hz"] = backend.AX25_MARK_HZ if backend is ax25 else rtty.RTTY_MARK_HZ
            meta["space_hz"] = backend.AX25_SPACE_HZ if backend is ax25 else rtty.RTTY_SPACE_HZ
        meta["num_samples"] = signal.size
        meta["samples_per_symbol"] = self.samples_per_symbol
        return signal, meta

    def decode_signal(
        self, signal: IqSamples
    ) -> tuple[
        PreambleField | None,
        MetadataField | None,
        int,
        bool,
        int,
        int,
        int,
    ] | None:
        body_len = self._burst_sample_len(include_metadata=True)
        search_len = min(
            len(signal),
            self._guard_silence_samples() + body_len + self.samples_per_symbol,
        )
        search = IqSamples(signal.data[:search_len])
        sync_start = self._correlate_sync(search)
        if sync_start is None:
            return None

        preamble_start = sync_start + self._sync_sample_len()
        bits = self._demodulate_preamble(signal, preamble_start, max_bits=24)
        codeword = bits_msb_first_to_codeword(bits)
        try:
            field, errors, valid = decode_preamble(codeword)
        except ValueError:
            return None, None, -1, False, codeword, sync_start, preamble_start

        metadata_field = None
        if field is not None and field.metadata_present:
            meta_bits = self._demodulate_preamble(
                signal, preamble_start, max_bits=24, skip_bits=24
            )
            meta_codeword = bits_msb_first_to_codeword(meta_bits)
            metadata_field, _, meta_valid = decode_metadata(meta_codeword)
            if not meta_valid:
                valid = False

        return field, metadata_field, errors, valid, codeword, sync_start, preamble_start

    def _burst_sample_len(self, include_metadata: bool = False) -> int:
        preamble_bits = 48 if include_metadata else 24
        if self.kind == "cpfsk4":
            return (len(fsk.bits_to_symbols(self.sync_bits)) + preamble_bits // 2) * self.samples_per_symbol
        return (len(self.sync_bits) + preamble_bits) * self.samples_per_symbol

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
            return self._fsk2_backend().correlate_sync(signal, sync, self.sample_rate)
        raise ValueError(f"unsupported modulation kind: {self.kind}")

    def _demodulate_preamble(
        self,
        signal: IqSamples,
        start: int,
        max_bits: int = 24,
        skip_bits: int = 0,
    ) -> list[int]:
        if self.kind == "cpfsk4":
            symbols_needed = (skip_bits + max_bits + 1) // 2
            symbols = fsk.demodulate_cpfsk(
                signal,
                self.deviations,
                sample_rate=self.sample_rate,
                start=start,
                max_symbols=symbols_needed,
            )
            bits = fsk.symbols_to_bits(symbols)
            return bits[skip_bits : skip_bits + max_bits]
        if self.kind == "bpsk":
            bits = psk.demodulate_bpsk(
                signal,
                sample_rate=self.sample_rate,
                start=start,
                max_symbols=max_bits + skip_bits,
            )
            return bits[skip_bits : skip_bits + max_bits]
        if self.kind == "fsk2":
            backend = self._fsk2_backend()
            bits = backend.demodulate_fsk2(
                signal,
                sample_rate=self.sample_rate,
                start=start,
                max_symbols=max_bits + skip_bits,
            )
            return bits[skip_bits : skip_bits + max_bits]
        raise ValueError(f"unsupported modulation kind: {self.kind}")
