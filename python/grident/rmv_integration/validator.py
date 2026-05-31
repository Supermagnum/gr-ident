"""Signal-layer validation via radio-modulation-validator."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .mode_map import EXCLUDED_FROM_SIGNAL_VALIDATION, KNOWN_AMBIGUITIES, get_rmv_expectation
from .preamble_check import PreambleCheckResult, check_preamble_roundtrip

logger = logging.getLogger(__name__)

RMV_INSTALL_URL = "https://github.com/Supermagnum/radio-modulation-validator"
RMV_SKIP_MESSAGE = (
    "WARNING: radio-modulation-validator not found. Signal-layer "
    "validation skipped. Install from:\n"
    f"  {RMV_INSTALL_URL}"
)


@dataclass
class SignalValidationResult:
    mode_id: int
    iq_file: Path
    rmv_available: bool
    skipped: bool
    skip_reason: str
    expected_family: str
    expected_order: str
    predicted_family: str
    predicted_order: str
    family_confidence: float
    order_confidence: float
    family_pass: bool
    order_pass: bool
    known_ambiguity: str
    notes: str


@dataclass
class ModeValidationResult:
    mode_id: int
    mode_name: str
    iq_file: Path | None
    preamble: PreambleCheckResult
    signal: SignalValidationResult | None
    overall_pass: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sibling_rmv_root() -> Path:
    return (_repo_root().parent / "radio-modulation-validator").resolve()


def find_rmv() -> Path | None:
    """Find the rmv executable (PATH, sibling venv, then None)."""
    which = shutil.which("rmv")
    if which:
        return Path(which)

    sibling = _sibling_rmv_root() / ".venv" / "bin" / "rmv"
    if sibling.is_file():
        return sibling

    return None


def rmv_importable() -> bool:
    """Return True if the rmv Python package can be imported."""
    try:
        import rmv  # noqa: F401
        return True
    except ImportError:
        pass

    sibling_src = _sibling_rmv_root() / "src"
    if sibling_src.is_dir() and str(sibling_src) not in sys.path:
        sys.path.insert(0, str(sibling_src))
        try:
            import rmv  # noqa: F401
            return True
        except ImportError:
            return False
    return False


def get_rmv_version(rmv_path: Path | None = None) -> str:
    """Return rmv version string or 'not available'."""
    rmv = rmv_path or find_rmv()
    if rmv is None:
        if rmv_importable():
            try:
                import rmv

                return getattr(rmv, "__version__", "importable (no CLI)")
            except ImportError:
                pass
        return "not available"

    try:
        proc = subprocess.run(
            [str(rmv), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in (proc.stdout + proc.stderr).splitlines():
            if "radio-modulation-validator" in line.lower() or "rmv" in line.lower():
                return line.strip()[:80]
    except (subprocess.SubprocessError, OSError):
        pass
    return str(rmv)


def _link_iq_file(src_cf32: Path, dest_iq: Path) -> None:
    """Symlink or copy .cf32 as .iq for rmv."""
    try:
        dest_iq.symlink_to(src_cf32.resolve())
    except OSError:
        shutil.copy2(src_cf32, dest_iq)


def _write_rmv_sidecar(
    sidecar_path: Path,
    mode_id: int,
    expected_family: str,
    expected_order: str,
) -> None:
    sidecar = {
        "source": "gr-ident",
        "block_name": f"mode_{mode_id:03d}",
        "expected_family": expected_family,
        "expected_order": expected_order,
        "sample_rate_hz": 48000,
        "center_freq_hz": 0,
        "snr_db": None,
        "notes": f"gr-ident test vector for mode_id={mode_id}",
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")


def _parse_rmv_json_output(stdout: str) -> dict[str, object]:
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {}


def _result_from_rmv_dict(
    mode_id: int,
    iq_file: Path,
    expected_family: str,
    expected_order: str,
    data: dict[str, object],
    *,
    rmv_available: bool = True,
    skipped: bool = False,
    skip_reason: str = "",
    notes: str = "",
) -> SignalValidationResult:
    if expected_family == "custom" and data.get("custom_mode"):
        custom = data["custom_mode"]
        if isinstance(custom, dict):
            conf = float(custom.get("confidence", 0.0))
            passed = bool(custom.get("pass_overall", False))
            return SignalValidationResult(
                mode_id=mode_id,
                iq_file=iq_file,
                rmv_available=rmv_available,
                skipped=skipped,
                skip_reason=skip_reason,
                expected_family="custom",
                expected_order=expected_order,
                predicted_family="custom",
                predicted_order=expected_order,
                family_confidence=conf,
                order_confidence=conf,
                family_pass=passed,
                order_pass=passed,
                known_ambiguity=KNOWN_AMBIGUITIES.get(mode_id, ""),
                notes=json.dumps(custom.get("metrics", {})),
            )

    return SignalValidationResult(
        mode_id=mode_id,
        iq_file=iq_file,
        rmv_available=rmv_available,
        skipped=skipped,
        skip_reason=skip_reason,
        expected_family=expected_family,
        expected_order=expected_order,
        predicted_family=str(data.get("predicted_family", "")),
        predicted_order=str(data.get("predicted_order", "")),
        family_confidence=float(data.get("family_confidence", 0.0)),
        order_confidence=float(data.get("order_confidence", 0.0)),
        family_pass=bool(data.get("family_pass", False)),
        order_pass=bool(data.get("order_pass", False)),
        known_ambiguity=KNOWN_AMBIGUITIES.get(mode_id, ""),
        notes=notes,
    )


def _run_rmv_subprocess(iq_file: Path, rmv: Path) -> dict[str, object]:
    proc = subprocess.run(
        [str(rmv), "validate", str(iq_file)],
        capture_output=True,
        text=True,
    )
    data = _parse_rmv_json_output(proc.stdout)
    if not data and proc.stderr:
        data = _parse_rmv_json_output(proc.stderr)
    return data


def _run_rmv_python_api(iq_file: Path) -> dict[str, object]:
    sibling_src = _sibling_rmv_root() / "src"
    if sibling_src.is_dir() and str(sibling_src) not in sys.path:
        sys.path.insert(0, str(sibling_src))

    from rmv.classifier import ModulationClassifier
    from rmv.validate import run_validate_file

    models_dir = _sibling_rmv_root() / "models"
    if not models_dir.is_dir():
        models_dir = Path.cwd() / "models"

    classifier = ModulationClassifier(
        models_dir,
        verify_checksums=False,
    )
    result = run_validate_file(
        iq_file,
        classifier,
        threshold=0.70,
        output_dir=Path(tempfile.gettempdir()) / "grident_rmv_out",
        verbose=False,
    )
    return result.to_dict()


def _invoke_rmv(
    tmp_iq: Path,
    rmv_path: Path | None,
) -> dict[str, object]:
    if rmv_path is not None:
        return _run_rmv_subprocess(tmp_iq, rmv_path)
    if rmv_importable():
        return _run_rmv_python_api(tmp_iq)
    return {}


def signal_passes(result: SignalValidationResult, *, signal_required: bool = False) -> bool:
    """Return True when signal validation succeeded or is acceptably skipped."""
    if result.skipped:
        if signal_required:
            return False
        return True
    if result.family_pass and result.order_pass:
        return True
    if result.known_ambiguity and result.family_pass:
        return True
    return False


def validate_iq_signal(
    mode_id: int,
    iq_file: Path,
    rmv_path: Path | None = None,
    fixture: dict[str, object] | None = None,
) -> SignalValidationResult:
    """Validate IQ file modulation against mode_id via rmv."""
    rmv = rmv_path or find_rmv()
    rmv_available = rmv is not None or rmv_importable()

    if mode_id in EXCLUDED_FROM_SIGNAL_VALIDATION:
        return SignalValidationResult(
            mode_id=mode_id,
            iq_file=iq_file,
            rmv_available=rmv_available,
            skipped=True,
            skip_reason="Mode excluded from signal validation",
            expected_family="",
            expected_order="",
            predicted_family="",
            predicted_order="",
            family_confidence=0.0,
            order_confidence=0.0,
            family_pass=False,
            order_pass=False,
            known_ambiguity="",
            notes="",
        )

    mapping = get_rmv_expectation(mode_id, fixture)
    if mapping is None:
        return SignalValidationResult(
            mode_id=mode_id,
            iq_file=iq_file,
            rmv_available=rmv_available,
            skipped=True,
            skip_reason=f"Mode {mode_id} not in rmv mode map",
            expected_family="",
            expected_order="",
            predicted_family="",
            predicted_order="",
            family_confidence=0.0,
            order_confidence=0.0,
            family_pass=False,
            order_pass=False,
            known_ambiguity="",
            notes="",
        )

    expected_family = mapping["family"]
    expected_order = mapping["order"]

    if not rmv_available:
        return SignalValidationResult(
            mode_id=mode_id,
            iq_file=iq_file,
            rmv_available=False,
            skipped=True,
            skip_reason="radio-modulation-validator not found",
            expected_family=expected_family,
            expected_order=expected_order,
            predicted_family="",
            predicted_order="",
            family_confidence=0.0,
            order_confidence=0.0,
            family_pass=False,
            order_pass=False,
            known_ambiguity=KNOWN_AMBIGUITIES.get(mode_id, ""),
            notes=f"Install rmv from {RMV_INSTALL_URL}",
        )

    with tempfile.TemporaryDirectory(prefix="grident_rmv_") as tmpdir:
        tmp = Path(tmpdir)
        tmp_iq = tmp / iq_file.with_suffix(".iq").name
        tmp_sidecar = tmp / (tmp_iq.stem + ".json")

        _link_iq_file(iq_file, tmp_iq)
        _write_rmv_sidecar(tmp_sidecar, mode_id, expected_family, expected_order)

        try:
            data = _invoke_rmv(tmp_iq, rmv)
        except Exception as exc:
            return SignalValidationResult(
                mode_id=mode_id,
                iq_file=iq_file,
                rmv_available=True,
                skipped=False,
                skip_reason="",
                expected_family=expected_family,
                expected_order=expected_order,
                predicted_family="",
                predicted_order="",
                family_confidence=0.0,
                order_confidence=0.0,
                family_pass=False,
                order_pass=False,
                known_ambiguity=KNOWN_AMBIGUITIES.get(mode_id, ""),
                notes=f"rmv error: {exc}",
            )

        if not data:
            return SignalValidationResult(
                mode_id=mode_id,
                iq_file=iq_file,
                rmv_available=True,
                skipped=False,
                skip_reason="",
                expected_family=expected_family,
                expected_order=expected_order,
                predicted_family="",
                predicted_order="",
                family_confidence=0.0,
                order_confidence=0.0,
                family_pass=False,
                order_pass=False,
                known_ambiguity=KNOWN_AMBIGUITIES.get(mode_id, ""),
                notes="rmv returned no JSON output",
            )

        return _result_from_rmv_dict(
            mode_id,
            iq_file,
            expected_family,
            expected_order,
            data,
        )


def _parse_codeword_hex(value: str) -> int:
    return int(value, 0)


def _load_fixture_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_mode(
    mode_id: int,
    fixture_dir: Path,
    rmv_path: Path | None = None,
    *,
    preamble_only: bool = False,
    signal_only: bool = False,
) -> ModeValidationResult:
    """Run preamble and/or signal validation for one mode fixture."""
    slug = f"mode_{mode_id:03d}"
    json_path = fixture_dir / f"{slug}.json"
    cf32_path = fixture_dir / f"{slug}.cf32"

    mode_name = f"Mode {mode_id}"
    fixture: dict[str, object] | None = None
    fixture_codeword: int | None = None

    if json_path.is_file():
        fixture = _load_fixture_json(json_path)
        mode_name = str(fixture.get("name", mode_name))
        hex_val = fixture.get("codeword_hex")
        if isinstance(hex_val, str):
            fixture_codeword = _parse_codeword_hex(hex_val)

    digital = bool(fixture.get("digital", False)) if fixture else mode_id >= 100
    encrypted = bool(fixture.get("encrypted", False)) if fixture else False
    metadata_present = bool(fixture.get("metadata_present", False)) if fixture else False

    if signal_only:
        preamble = PreambleCheckResult(
            mode_id=mode_id,
            digital=digital,
            encrypted=encrypted,
            metadata_present=metadata_present,
            encoded_codeword=0,
            decoded_ok=True,
            bit_errors_corrected=0,
            field_matches_fixture=True,
            notes="skipped (--signal-only)",
        )
    else:
        preamble = check_preamble_roundtrip(
            mode_id,
            digital,
            encrypted,
            metadata_present,
            fixture_codeword=fixture_codeword,
        )

    signal: SignalValidationResult | None = None
    iq_file: Path | None = cf32_path if cf32_path.is_file() else None

    if not preamble_only and iq_file is not None:
        signal = validate_iq_signal(mode_id, iq_file, rmv_path, fixture=fixture)
    elif not preamble_only and iq_file is None:
        signal = SignalValidationResult(
            mode_id=mode_id,
            iq_file=cf32_path,
            rmv_available=find_rmv() is not None or rmv_importable(),
            skipped=True,
            skip_reason="IQ fixture file not found",
            expected_family="",
            expected_order="",
            predicted_family="",
            predicted_order="",
            family_confidence=0.0,
            order_confidence=0.0,
            family_pass=False,
            order_pass=False,
            known_ambiguity="",
            notes=f"Missing {cf32_path.name}",
        )

    preamble_ok = preamble.decoded_ok and preamble.field_matches_fixture
    signal_ok = signal is None or signal_passes(signal, signal_required=signal_only)
    overall_pass = preamble_ok and signal_ok

    return ModeValidationResult(
        mode_id=mode_id,
        mode_name=mode_name,
        iq_file=iq_file,
        preamble=preamble,
        signal=signal,
        overall_pass=overall_pass,
    )


def discover_fixture_mode_ids(fixture_dir: Path) -> list[int]:
    """Return sorted mode IDs from JSON fixtures in fixture_dir."""
    ids: list[int] = []
    for path in sorted(fixture_dir.glob("mode_*.json")):
        try:
            data = _load_fixture_json(path)
            mode_id = int(data["mode_id"])
            ids.append(mode_id)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return ids


def print_rmv_missing_warning() -> None:
    """Print standard warning when rmv is not available."""
    if find_rmv() is None and not rmv_importable():
        print(RMV_SKIP_MESSAGE, file=sys.stderr)
