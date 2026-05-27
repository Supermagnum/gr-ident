"""Preamble field pack/unpack and Golay wrapping."""

from __future__ import annotations

from dataclasses import dataclass

from .golay import decode_golay24, encode_golay24


@dataclass
class PreambleField:
    mode_id: int = 0
    encrypted: bool = False
    digital: bool = False


def pack_field(field: PreambleField) -> int:
    if field.mode_id < 0 or field.mode_id > 511:
        raise ValueError("mode_id must be 0..511")
    raw = field.mode_id & 0x1FF
    if field.encrypted:
        raw |= 1 << 10
    if field.digital:
        raw |= 1 << 11
    return raw


def unpack_field(raw_12: int, strict_reserved: bool = True) -> PreambleField:
    if strict_reserved and ((raw_12 >> 9) & 1):
        raise ValueError("reserved bit 9 must be zero")
    return PreambleField(
        mode_id=raw_12 & 0x1FF,
        encrypted=bool((raw_12 >> 10) & 1),
        digital=bool((raw_12 >> 11) & 1),
    )


def encode_preamble(field: PreambleField) -> int:
    return encode_golay24(pack_field(field))


def decode_preamble(codeword_24: int) -> tuple[PreambleField | None, int, bool]:
    data, errors, valid = decode_golay24(codeword_24)
    if not valid:
        return None, errors, False
    return unpack_field(data), errors, True


def codeword_to_bits_msb_first(codeword_24: int) -> list[int]:
    return [(codeword_24 >> (23 - i)) & 1 for i in range(24)]


def bits_msb_first_to_codeword(bits: list[int]) -> int:
    codeword = 0
    for bit in bits[:24]:
        codeword = (codeword << 1) | (bit & 1)
    for _ in range(max(0, 24 - len(bits))):
        codeword <<= 1
    return codeword
