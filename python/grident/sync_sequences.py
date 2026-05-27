"""Normative gr-ident synchronization sequences (single source of truth)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncSequence:
    """Binary sync pattern transmitted MSB-first before the Golay preamble."""

    name: str
    bits: tuple[int, ...]
    reference: str

    @property
    def length(self) -> int:
        return len(self.bits)

    def as_binary_string(self) -> str:
        return "".join(str(b & 1) for b in self.bits)

    def as_hex(self) -> str:
        value = 0
        for bit in self.bits:
            value = (value << 1) | (bit & 1)
        width = (self.length + 3) // 4
        return f"0x{value:0{width}X}"


# NFM / EchoLink family: 16-bit (4800 sym/s CPFSK 4-FSK on 12.5 kHz channel)
SYNC_NFM = SyncSequence(
    name="sync_nfm",
    bits=(0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0),
    reference="gr-ident assigned; used by nfm_125_* profiles",
)

SYNC_C4FM = SyncSequence(
    name="sync_c4fm",
    bits=(
        1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
    ),
    reference="gr-ident assigned (Fusion-style delimiter)",
)

SYNC_DPMR = SyncSequence(
    name="sync_dpmr",
    bits=(
        1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0,
    ),
    reference="gr-ident assigned (dPMR-style)",
)

SYNC_DMR = SyncSequence(
    name="sync_dmr",
    bits=(
        1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0,
    ),
    reference="gr-ident assigned (DMR air-interface family)",
)

SYNC_NXDN = SyncSequence(
    name="sync_nxdn",
    bits=(0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1),
    reference="gr-ident assigned (NXDN narrowband digital)",
)

SYNC_M17 = SyncSequence(
    name="sync_m17",
    bits=(0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0),
    reference="gr-ident assigned (M17 open digital voice)",
)

SYNC_DSTAR = SyncSequence(
    name="sync_dstar",
    bits=(1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1),
    reference="gr-ident assigned (D-STAR gateway path; test vectors use 4-FSK)",
)

SYNC_PSK31 = SyncSequence(
    name="sync_psk31",
    bits=(1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0),
    reference="gr-ident assigned (BPSK 31.25 baud)",
)

SYNC_RTTY = SyncSequence(
    name="sync_rtty",
    bits=(0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1),
    reference="gr-ident assigned (2-FSK 50 baud RTTY)",
)

SYNC_AX25 = SyncSequence(
    name="sync_ax25",
    bits=(0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1),
    reference="gr-ident assigned (Bell 202 AFSK 1200 baud packet)",
)

ALL_SYNC_SEQUENCES: tuple[SyncSequence, ...] = (
    SYNC_NFM,
    SYNC_C4FM,
    SYNC_DPMR,
    SYNC_DMR,
    SYNC_NXDN,
    SYNC_M17,
    SYNC_DSTAR,
    SYNC_PSK31,
    SYNC_RTTY,
    SYNC_AX25,
)

SYNC_BY_NAME = {seq.name: seq for seq in ALL_SYNC_SEQUENCES}
