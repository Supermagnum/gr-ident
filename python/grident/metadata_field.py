"""Optional secondary Golay-protected metadata field."""

from __future__ import annotations

from dataclasses import dataclass

from .golay import decode_golay24, encode_golay24

# Bandwidth codes (4 bits, bits 11-8 of the 12-bit metadata field)
BANDWIDTH_UNSPECIFIED = 0
BANDWIDTH_6_25_KHZ = 1
BANDWIDTH_8_33_KHZ = 2
BANDWIDTH_12_5_KHZ = 3
BANDWIDTH_20_KHZ = 4
BANDWIDTH_25_KHZ = 5
BANDWIDTH_WFM = 6

BANDWIDTH_NAMES = {
    BANDWIDTH_UNSPECIFIED: "unspecified",
    BANDWIDTH_6_25_KHZ: "6.25 kHz",
    BANDWIDTH_8_33_KHZ: "8.33 kHz",
    BANDWIDTH_12_5_KHZ: "12.5 kHz",
    BANDWIDTH_20_KHZ: "20 kHz",
    BANDWIDTH_25_KHZ: "25 kHz",
    BANDWIDTH_WFM: "WFM / wide",
}


@dataclass
class MetadataField:
    """Secondary 12-bit field: bandwidth, codec sub-parameter, callsign hint."""

    bandwidth_code: int = BANDWIDTH_UNSPECIFIED
    codec_param: int = 0
    callsign_nibble: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.bandwidth_code <= 15:
            raise ValueError("bandwidth_code must be 0..15")
        if not 0 <= self.codec_param <= 15:
            raise ValueError("codec_param must be 0..15")
        if not 0 <= self.callsign_nibble <= 15:
            raise ValueError("callsign_nibble must be 0..15")


def pack_metadata(field: MetadataField) -> int:
    return (
        ((field.bandwidth_code & 0xF) << 8)
        | ((field.codec_param & 0xF) << 4)
        | (field.callsign_nibble & 0xF)
    )


def unpack_metadata(raw_12: int) -> MetadataField:
    return MetadataField(
        bandwidth_code=(raw_12 >> 8) & 0xF,
        codec_param=(raw_12 >> 4) & 0xF,
        callsign_nibble=raw_12 & 0xF,
    )


def encode_metadata(field: MetadataField) -> int:
    return encode_golay24(pack_metadata(field))


def decode_metadata(codeword_24: int) -> tuple[MetadataField | None, int, bool]:
    data, errors, valid = decode_golay24(codeword_24)
    if not valid:
        return None, errors, False
    return unpack_metadata(data), errors, True


def callsign_crc_nibble(callsign: str) -> int:
    """Upper 4 bits of CRC-16-CCITT over the callsign (0 if empty)."""
    if not callsign:
        return 0
    crc = 0xFFFF
    for ch in callsign.upper().encode("ascii"):
        crc ^= ch << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return (crc >> 12) & 0xF
