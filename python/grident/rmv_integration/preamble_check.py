"""Golay preamble roundtrip validation (no rmv dependency)."""

from __future__ import annotations

from dataclasses import dataclass

from grident.golay import decode_golay24, encode_golay24
from grident.preamble import PreambleField, pack_field, unpack_field


@dataclass
class PreambleCheckResult:
    mode_id: int
    digital: bool
    encrypted: bool
    metadata_present: bool
    encoded_codeword: int
    decoded_ok: bool
    bit_errors_corrected: int
    field_matches_fixture: bool
    notes: str


def _field_from_args(
    mode_id: int,
    digital: bool,
    encrypted: bool,
    metadata_present: bool,
) -> PreambleField:
    return PreambleField(
        mode_id=mode_id,
        digital=digital,
        encrypted=encrypted,
        metadata_present=metadata_present,
    )


def check_preamble_roundtrip(
    mode_id: int,
    digital: bool,
    encrypted: bool,
    metadata_present: bool,
    fixture_codeword: int | None = None,
) -> PreambleCheckResult:
    """Encode the preamble field, Golay-encode, decode, and verify round-trip."""
    field = _field_from_args(mode_id, digital, encrypted, metadata_present)
    packed = pack_field(field)
    codeword = encode_golay24(packed)

    fixture_match = codeword == fixture_codeword if fixture_codeword is not None else True

    decoded_packed, errors, valid = decode_golay24(codeword)
    if not valid:
        return PreambleCheckResult(
            mode_id=mode_id,
            digital=digital,
            encrypted=encrypted,
            metadata_present=metadata_present,
            encoded_codeword=codeword,
            decoded_ok=False,
            bit_errors_corrected=errors,
            field_matches_fixture=fixture_match,
            notes="Golay decode failed on clean codeword",
        )

    unpacked = unpack_field(decoded_packed, strict_reserved=False)
    decoded_ok = (
        unpacked.mode_id == mode_id
        and unpacked.digital == digital
        and unpacked.encrypted == encrypted
        and unpacked.metadata_present == metadata_present
    )

    return PreambleCheckResult(
        mode_id=mode_id,
        digital=digital,
        encrypted=encrypted,
        metadata_present=metadata_present,
        encoded_codeword=codeword,
        decoded_ok=decoded_ok,
        bit_errors_corrected=errors,
        field_matches_fixture=fixture_match,
        notes="" if decoded_ok else "Field mismatch after Golay roundtrip",
    )


def check_preamble_with_errors(
    mode_id: int,
    digital: bool,
    encrypted: bool,
    metadata_present: bool,
    n_errors: int,
) -> PreambleCheckResult:
    """Inject n_errors bit flips and verify correction behaviour."""
    field = _field_from_args(mode_id, digital, encrypted, metadata_present)
    packed = pack_field(field)
    codeword = encode_golay24(packed)

    corrupted = codeword
    for i in range(n_errors):
        corrupted ^= 1 << i

    decoded_packed, errors_corrected, valid = decode_golay24(corrupted)
    if not valid:
        return PreambleCheckResult(
            mode_id=mode_id,
            digital=digital,
            encrypted=encrypted,
            metadata_present=metadata_present,
            encoded_codeword=codeword,
            decoded_ok=False,
            bit_errors_corrected=errors_corrected,
            field_matches_fixture=True,
            notes=f"{n_errors} bit errors injected; uncorrectable",
        )

    unpacked = unpack_field(decoded_packed, strict_reserved=False)
    decoded_ok = (
        n_errors <= 3
        and unpacked.mode_id == mode_id
        and unpacked.digital == digital
        and unpacked.encrypted == encrypted
        and unpacked.metadata_present == metadata_present
    )

    return PreambleCheckResult(
        mode_id=mode_id,
        digital=digital,
        encrypted=encrypted,
        metadata_present=metadata_present,
        encoded_codeword=codeword,
        decoded_ok=decoded_ok,
        bit_errors_corrected=errors_corrected,
        field_matches_fixture=True,
        notes=f"{n_errors} bit errors injected; "
        f"{'corrected' if decoded_ok else 'uncorrectable'}",
    )
