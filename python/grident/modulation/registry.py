"""Registered modulation profiles and mode ID mapping."""

from __future__ import annotations

from .fsk import DEFAULT_SAMPLE_RATE
from .profile import ModulationProfile
from .psk import PSK31_BAUD
from .rtty import RTTY_BAUD
from .ax25 import AX25_BAUD
from .squelch import ctcss_overlay, dcs_overlay
from ..sync_sequences import (
    SYNC_AX25,
    SYNC_C4FM,
    SYNC_DMR,
    SYNC_DPMR,
    SYNC_DSTAR,
    SYNC_M17,
    SYNC_NFM,
    SYNC_NXDN,
    SYNC_PSK31,
    SYNC_RTTY,
)

DEV_ETSI_NB = (648.0, 1944.0)

NFM_125_4800 = ModulationProfile(
    name="nfm_125_4800",
    description="NFM 12.5 kHz channel, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI EN 300 113 (12.5 kHz channel); 4-FSK deviations per ETSI TS 102 490",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NFM.bits,
)

NFM_125_CTCSS_4800 = ModulationProfile(
    name="nfm_125_ctcss_4800",
    description="NFM 12.5 kHz + CTCSS 88.5 Hz, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI EN 300 113; EIA/TIA-603 CTCSS; 4-FSK per ETSI TS 102 490",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NFM.bits,
    overlay_builder=ctcss_overlay,
)

NFM_125_DCS_4800 = ModulationProfile(
    name="nfm_125_dcs_4800",
    description="NFM 12.5 kHz + DCS, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI EN 300 113; ETSI TS 103 236 DCS; 4-FSK per ETSI TS 102 490",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NFM.bits,
    overlay_builder=dcs_overlay,
)

C4FM_4800 = ModulationProfile(
    name="c4fm_4800",
    description="Yaesu System Fusion C4FM, 4800 sym/s 4-FSK",
    reference="Yaesu System Fusion / C4FM amateur digital voice air interface",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_C4FM.bits,
)

DPMR_4800 = ModulationProfile(
    name="dpmr_4800",
    description="dPMR Phase 1, 4800 sym/s 4-FSK",
    reference="ETSI TS 102 490-1 (dPMR air interface)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_DPMR.bits,
)

DMR_4800 = ModulationProfile(
    name="dmr_4800",
    description="DMR family, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI TS 102 361 (DMR air interface)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_DMR.bits,
)

NXDN_4800 = ModulationProfile(
    name="nxdn_4800",
    description="NXDN narrowband digital, 4800 sym/s 4-FSK preamble burst",
    reference="NXDN common air interface (Icom / Kenwood)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NXDN.bits,
)

M17_4800 = ModulationProfile(
    name="m17_4800",
    description="M17 open digital voice, 4800 sym/s 4-FSK preamble burst",
    reference="M17 open digital voice protocol",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_M17.bits,
)

DSTAR_4800 = ModulationProfile(
    name="dstar_4800",
    description="D-STAR gateway path, 4800 sym/s 4-FSK test-vector preamble",
    reference="D-STAR digital voice (test vectors use 4-FSK placeholder)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_DSTAR.bits,
)

PSK31_3125 = ModulationProfile(
    name="psk31_3125",
    description="PSK31 BPSK preamble burst at 31.25 baud",
    reference="PSK31 amateur digital mode (BPSK, 31.25 baud Varicode payload)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    sync_bits=SYNC_PSK31.bits,
    kind="bpsk",
    symbol_rate=PSK31_BAUD,
)

RTTY_50 = ModulationProfile(
    name="rtty_50",
    description="RTTY 2-FSK preamble burst at 50 baud, 170 Hz shift",
    reference="ITA2 radioteletype (50 baud, 170 Hz frequency shift)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    sync_bits=SYNC_RTTY.bits,
    kind="fsk2",
    symbol_rate=RTTY_BAUD,
)

AX25_1200 = ModulationProfile(
    name="ax25_1200",
    description="AX.25 Bell 202 AFSK preamble burst at 1200 baud",
    reference="AX.25 amateur packet (Bell 202 1200/2200 Hz AFSK)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    sync_bits=SYNC_AX25.bits,
    kind="fsk2",
    symbol_rate=AX25_BAUD,
)

ALL_PROFILES: tuple[ModulationProfile, ...] = (
    NFM_125_4800,
    NFM_125_CTCSS_4800,
    NFM_125_DCS_4800,
    C4FM_4800,
    DPMR_4800,
    DMR_4800,
    NXDN_4800,
    M17_4800,
    DSTAR_4800,
    PSK31_3125,
    RTTY_50,
    AX25_1200,
)

PROFILE_BY_NAME = {profile.name: profile for profile in ALL_PROFILES}

PROFILE_BY_MODE_ID: dict[int, ModulationProfile] = {
    20: NFM_125_4800,
    21: NFM_125_4800,
    22: NFM_125_4800,
    30: NFM_125_CTCSS_4800,
    31: NFM_125_CTCSS_4800,
    32: NFM_125_CTCSS_4800,
    40: NFM_125_DCS_4800,
    41: NFM_125_DCS_4800,
    42: NFM_125_DCS_4800,
    100: DMR_4800,
    101: DMR_4800,
    102: DMR_4800,
    103: DSTAR_4800,
    104: C4FM_4800,
    105: C4FM_4800,
    106: DMR_4800,
    107: NXDN_4800,
    108: DPMR_4800,
    109: DMR_4800,
    110: NFM_125_4800,
    111: NFM_125_4800,
    112: NFM_125_4800,
    113: NFM_125_4800,
    114: C4FM_4800,
    115: DSTAR_4800,
    120: M17_4800,
    121: M17_4800,
    122: PSK31_3125,
    123: PSK31_3125,
    124: PSK31_3125,
    150: AX25_1200,
    151: AX25_1200,
    152: PSK31_3125,
    153: NFM_125_4800,
    154: PSK31_3125,
    158: PSK31_3125,
    159: RTTY_50,
}


def get_profile(name: str) -> ModulationProfile:
    try:
        return PROFILE_BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"unknown modulation profile: {name}") from exc


def get_profile_for_mode(mode_id: int) -> ModulationProfile:
    try:
        return PROFILE_BY_MODE_ID[mode_id]
    except KeyError as exc:
        raise KeyError(f"no modulation profile assigned for mode_id {mode_id}") from exc


def list_profiles() -> list[str]:
    return [profile.name for profile in ALL_PROFILES]


def list_assigned_mode_ids() -> list[int]:
    return sorted(PROFILE_BY_MODE_ID)
