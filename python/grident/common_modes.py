"""Common mode IDs used for IQ identification regression tests."""

from __future__ import annotations

from dataclasses import dataclass

from .modulation.registry import PROFILE_BY_MODE_ID, get_profile_for_mode
from .preamble import PreambleField


@dataclass(frozen=True)
class CommonMode:
    mode_id: int
    name: str
    digital: bool
    profile_name: str

    @property
    def slug(self) -> str:
        return f"mode_{self.mode_id:03d}"

    def to_field(self) -> PreambleField:
        return PreambleField(mode_id=self.mode_id, encrypted=False, digital=self.digital)


def _profile_name(mode_id: int) -> str:
    return get_profile_for_mode(mode_id).name


COMMON_MODES: tuple[CommonMode, ...] = (
    CommonMode(20, "NFM 12.5 kHz", False, _profile_name(20)),
    CommonMode(30, "NFM 12.5 kHz + CTCSS", False, _profile_name(30)),
    CommonMode(40, "NFM 12.5 kHz + DCS", False, _profile_name(40)),
    CommonMode(104, "C4FM / Fusion", True, _profile_name(104)),
    CommonMode(108, "dPMR", True, _profile_name(108)),
    CommonMode(110, "EchoLink", True, _profile_name(110)),
    CommonMode(158, "PSK31", True, _profile_name(158)),
    CommonMode(159, "RTTY", True, _profile_name(159)),
)

COMMON_MODE_BY_ID = {mode.mode_id: mode for mode in COMMON_MODES}
