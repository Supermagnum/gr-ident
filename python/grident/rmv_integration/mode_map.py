"""Maps gr-ident mode_id values to radio-modulation-validator classifier labels."""

from __future__ import annotations

# Maps gr-ident mode_id to rmv expected_family and expected_order.
# Only modes with committed IQ test vectors need entries here.
# Modes without IQ test vectors are skipped in signal validation.
MODE_TO_RMV: dict[int, dict[str, str]] = {
    # Analog FM modes
    20: {"family": "FM", "order": "NBFM_25"},
    21: {"family": "FM", "order": "NBFM_25"},  # default; see get_rmv_expectation()
    22: {"family": "FM", "order": "NBFM_25"},
    30: {"family": "FM", "order": "NBFM_25"},
    40: {"family": "FM", "order": "NBFM_25"},
    10: {"family": "FM", "order": "WBFM"},
    12: {"family": "FM", "order": "NBFM_50"},
    # Analog AM modes (mode 21 aviation AM uses fixture override)
    1: {"family": "AM", "order": "AM-DSB"},
    2: {"family": "AM", "order": "AM-DSB"},
    3: {"family": "AM", "order": "AM-SSB"},
    4: {"family": "AM", "order": "AM-SSB"},
    5: {"family": "AM", "order": "AM-SSB"},
    # Digital voice - 4FSK family
    100: {"family": "FSK", "order": "DMR"},
    101: {"family": "FSK", "order": "DMR"},
    102: {"family": "FSK", "order": "DMR"},
    103: {"family": "FSK", "order": "GMSK"},
    104: {"family": "FSK", "order": "YSF"},
    105: {"family": "FSK", "order": "CPFSK"},
    107: {"family": "FSK", "order": "NXDN"},
    108: {"family": "FSK", "order": "dPMR"},
    110: {"family": "FSK", "order": "CPFSK"},
    120: {"family": "FSK", "order": "M17"},
    121: {"family": "FSK", "order": "M17"},
    # Data / packet
    150: {"family": "FSK", "order": "CPFSK"},
    151: {"family": "FSK", "order": "CPFSK"},
    158: {"family": "PSK", "order": "BPSK"},
    159: {"family": "FSK", "order": "2FSK"},
    # Experimental
    300: {"family": "custom", "order": "sleipnir_8qpsk"},
}

VALID_FAMILIES = frozenset({"FM", "FSK", "PSK", "QAM", "AM", "PAM", "custom"})

# Fixture-driven override when mode 21 appears as aviation AM in a test vector.
AVIATION_AM_EXPECTATION = {"family": "AM", "order": "AM_AIR_833"}

# Known ambiguities - soft-fail only, not hard-fail
KNOWN_AMBIGUITIES: dict[int, str] = {
    107: "NXDN and dPMR have identical modulation parameters",
    21: "Mode 21 may be aviation AM or NFM depending on context",
}

# Modes explicitly excluded from signal validation
EXCLUDED_FROM_SIGNAL_VALIDATION: set[int] = {
    0,
    60,
    109,
    511,
}


def get_rmv_expectation(
    mode_id: int,
    fixture: dict[str, object] | None = None,
) -> dict[str, str] | None:
    """Return rmv family/order for mode_id, applying fixture overrides when needed."""
    if mode_id in EXCLUDED_FROM_SIGNAL_VALIDATION:
        return None
    if mode_id not in MODE_TO_RMV:
        return None

    mapping = dict(MODE_TO_RMV[mode_id])
    if mode_id == 21 and fixture is not None:
        profile = str(fixture.get("profile", "")).lower()
        name = str(fixture.get("name", "")).lower()
        modulation = str(fixture.get("modulation", "")).lower()
        if (
            "am_air" in profile
            or modulation.startswith("am")
            or ("aviation" in name and "am" in name)
        ):
            return dict(AVIATION_AM_EXPECTATION)
    return mapping
