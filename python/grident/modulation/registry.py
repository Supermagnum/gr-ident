"""Registered modulation profiles and mode ID mapping."""

from __future__ import annotations

from .fsk import DEFAULT_SAMPLE_RATE
from .profile import ModulationProfile
from .psk import PSK31_BAUD
from .rtty import RTTY_BAUD
from .squelch import ctcss_overlay, dcs_overlay

# NFM family sync: 16-bit correlator sequence (4800 sym/s CPFSK data burst on 12.5 kHz FM)
SYNC_NFM: tuple[int, ...] = (0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0)

# C4FM / System Fusion: 24-bit sync (Yaesu DN-style frame delimiter, gr-ident assigned)
SYNC_C4FM: tuple[int, ...] = (
    1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
)

# dPMR: 24-bit sync (ETSI TS 102 490 physical layer, gr-ident assigned)
SYNC_DPMR: tuple[int, ...] = (
    1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0,
)

# PSK31: 16-bit sync (gr-ident assigned, BPSK 31.25 baud)
SYNC_PSK31: tuple[int, ...] = (
    1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0,
)

# RTTY: 16-bit sync (gr-ident assigned, 2-FSK 50 baud)
SYNC_RTTY: tuple[int, ...] = (
    0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1,
)

# ETSI / Yaesu narrowband 4-FSK deviations (Hz): low tier, high tier
DEV_ETSI_NB = (648.0, 1944.0)

NFM_125_4800 = ModulationProfile(
    name="nfm_125_4800",
    description="NFM 12.5 kHz channel, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI EN 300 113 (12.5 kHz channel); 4-FSK deviations per ETSI TS 102 490",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NFM,
)

NFM_125_CTCSS_4800 = ModulationProfile(
    name="nfm_125_ctcss_4800",
    description="NFM 12.5 kHz + CTCSS 88.5 Hz, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI EN 300 113; EIA/TIA-603 CTCSS; 4-FSK per ETSI TS 102 490",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NFM,
    overlay_builder=ctcss_overlay,
)

NFM_125_DCS_4800 = ModulationProfile(
    name="nfm_125_dcs_4800",
    description="NFM 12.5 kHz + DCS, 4800 sym/s 4-FSK preamble burst",
    reference="ETSI EN 300 113; ETSI TS 103 236 DCS; 4-FSK per ETSI TS 102 490",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_NFM,
    overlay_builder=dcs_overlay,
)

C4FM_4800 = ModulationProfile(
    name="c4fm_4800",
    description="Yaesu System Fusion C4FM, 4800 sym/s 4-FSK",
    reference="Yaesu System Fusion / C4FM amateur digital voice air interface",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_C4FM,
)

DPMR_4800 = ModulationProfile(
    name="dpmr_4800",
    description="dPMR Phase 1, 4800 sym/s 4-FSK",
    reference="ETSI TS 102 490-1 (dPMR air interface)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    deviations=DEV_ETSI_NB,
    sync_bits=SYNC_DPMR,
)

PSK31_3125 = ModulationProfile(
    name="psk31_3125",
    description="PSK31 BPSK preamble burst at 31.25 baud",
    reference="PSK31 amateur digital mode (BPSK, 31.25 baud Varicode payload)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    sync_bits=SYNC_PSK31,
    kind="bpsk",
    symbol_rate=PSK31_BAUD,
)

RTTY_50 = ModulationProfile(
    name="rtty_50",
    description="RTTY 2-FSK preamble burst at 50 baud, 170 Hz shift",
    reference="ITA2 radioteletype (50 baud, 170 Hz frequency shift)",
    sample_rate=DEFAULT_SAMPLE_RATE,
    sync_bits=SYNC_RTTY,
    kind="fsk2",
    symbol_rate=RTTY_BAUD,
)

ALL_PROFILES: tuple[ModulationProfile, ...] = (
    NFM_125_4800,
    NFM_125_CTCSS_4800,
    NFM_125_DCS_4800,
    C4FM_4800,
    DPMR_4800,
    PSK31_3125,
    RTTY_50,
)

PROFILE_BY_NAME = {profile.name: profile for profile in ALL_PROFILES}

# Mode ID -> profile for common test modes and spec defaults
PROFILE_BY_MODE_ID: dict[int, ModulationProfile] = {
    20: NFM_125_4800,
    30: NFM_125_CTCSS_4800,
    40: NFM_125_DCS_4800,
    104: C4FM_4800,
    108: DPMR_4800,
    110: NFM_125_4800,  # EchoLink: FM repeater / gateway path
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
