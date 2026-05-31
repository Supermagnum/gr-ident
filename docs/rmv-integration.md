# radio-modulation-validator Integration

gr-ident uses [radio-modulation-validator](https://github.com/Supermagnum/radio-modulation-validator)
to verify that IQ test vectors contain the modulation claimed by each mode ID.

## Two-layer validation

### Layer 1: Preamble (Golay roundtrip)

Verifies the gr-ident specification itself:

- 12-bit field packs correctly from `(mode_id, digital, encrypted, metadata_present)`
- Golay(24,12) encoder produces the codeword committed in fixture JSON
- Golay decoder recovers the field from the codeword
- Up to 3 injected bit errors are corrected
- 4 bit errors are correctly detected as uncorrectable

### Layer 2: Signal (rmv classifier)

Verifies the IQ test vectors:

- The `.cf32` fixture file for each mode is classified by rmv (via temporary `.iq` symlink)
- Expected modulation family (FM/FSK/PSK/AM/QAM) must match `mode_id`
- Expected modulation order (NBFM_25/DMR/M17/etc.) must match where known

## Running validation

```bash
PYTHONPATH=python python3 apps/grident_validate.py \
  --fixtures python/tests/fixtures/common_modes/
```

Preamble-only (no rmv required):

```bash
PYTHONPATH=python python3 apps/grident_validate.py --preamble-only
```

Results are written to `docs/validation-report.md` (gitignored; see `docs/validation-report-example.md`).

## rmv detection order

1. `rmv` command on `PATH`
2. `../radio-modulation-validator/.venv/bin/rmv` (sibling checkout)
3. Import `rmv` as a Python package (sibling `src/` added to `sys.path`)

If rmv is not found, signal-layer validation is skipped with:

```
WARNING: radio-modulation-validator not found. Signal-layer
validation skipped. Install from:
  https://github.com/Supermagnum/radio-modulation-validator
```

## Validation boundary

radio-modulation-validator uses reference signals generated independently
from gr-ident blocks. The rmv training data comes from:

- RadioML 2016.10A (DeepSig)
- CSPB.ML.2018R2 (cyclostationary.blog)
- Synthetic signals from GNU Radio built-in blocks and numpy/scipy only

gr-ident IQ test vectors are what is being validated. rmv is the
independent reference. The boundary is clean.

## Known soft fails

Some mode IDs produce correct signals that rmv cannot distinguish at
order level due to identical modulation parameters:

| Mode | Expected | Predicted | Reason |
|---|---|---|---|
| 107 (NXDN) | NXDN | dPMR | Identical 2400 baud 4FSK waveform |
| 21 | NFM or AM | context-dependent | Aviation AM vs NFM 8.33 kHz |

These are documented in `KNOWN_AMBIGUITIES` in `mode_map.py` and are
treated as passes when family matches.

## Repeater runtime fallback

For live receive on the SDR-repeater, see `backend.py`, `runtime.py`, and
`identify.py`. Preamble always controls routing; the classifier is advisory
only and never blocks audio.

| Mode | Preamble | Classifier | Backend |
|---|---|---|---|
| Full | yes | yes | NPU (SpacemiT A100) |
| Degraded | yes | yes | CPU (ONNX) |
| Minimal | yes | no | None |
| Fallback | no | no | None |

Startup status is published on the ZeroMQ status socket via `RuntimeStatus.to_zmq_status()`.
