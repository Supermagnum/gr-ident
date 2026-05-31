"""radio-modulation-validator integration for gr-ident validation and runtime."""

from .cli import main
from .identify import IdentificationResult, identify_signal
from .mode_map import KNOWN_AMBIGUITIES, MODE_TO_RMV, get_rmv_expectation
from .preamble_check import PreambleCheckResult, check_preamble_roundtrip, check_preamble_with_errors
from .report import generate_report, write_report
from .runtime import IdentificationMode, RuntimeStatus, initialise_runtime
from .validator import (
    ModeValidationResult,
    SignalValidationResult,
    discover_fixture_mode_ids,
    find_rmv,
    validate_iq_signal,
    validate_mode,
)

__all__ = [
    "KNOWN_AMBIGUITIES",
    "MODE_TO_RMV",
    "IdentificationMode",
    "IdentificationResult",
    "ModeValidationResult",
    "PreambleCheckResult",
    "RuntimeStatus",
    "SignalValidationResult",
    "check_preamble_roundtrip",
    "check_preamble_with_errors",
    "discover_fixture_mode_ids",
    "find_rmv",
    "generate_report",
    "get_rmv_expectation",
    "identify_signal",
    "initialise_runtime",
    "main",
    "validate_iq_signal",
    "validate_mode",
    "write_report",
]
