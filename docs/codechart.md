# gr-ident Code Chart

Debug reference: where to find implementation code, tests, and IQ generation.

---

## Repository layout

```
gr-ident/
├── README.md                          Spec + mode table
├── apps/
│   └── grident_iq_test.py             CLI: decode one .cf32 capture
├── blocklib/grident/
│   ├── include/gnuradio/grident/      C++ public headers
│   ├── lib/                             C++ core (Golay, preamble, mode table)
│   ├── test/                            C++ unit tests (Meson)
│   └── blocks/                        GNU Radio 4 block stubs
├── build-gr4/                           GR4 plugin build (CMake)
├── python/
│   ├── grident/                         Python library
│   └── tests/                           Python unit tests + IQ fixtures
├── test_iq/vectors/common/             Generated .cf32 + .json (dev vectors)
└── docs/                                Generated documentation and plots
```

Set `PYTHONPATH=python` for all Python commands below.

---

## IQ generation pipeline

```
PreambleField (mode_id, digital, encrypted)
        │
        ▼
get_profile_for_mode()          registry.py
        │
        ▼
ModulationProfile.modulate_preamble()   profile.py
        ├── fsk.modulate_cpfsk()        cpfsk4 profiles (NFM, C4FM, dPMR)
        ├── psk.modulate_bpsk()         PSK31
        ├── rtty.modulate_fsk2()          RTTY
        └── squelch overlays            CTCSS/DCS tail only (modes 30, 40)
        │
        ▼
IqSamples + metadata dict
        │
        ├── write_cf32() / IqSamples.tofile()     iq_samples.py
        └── sidecar .json
```

### Entry points (generate IQ files)

| Script | Purpose | Output |
|---|---|---|
| `python/grident/generate_common_modes.py` | All 8 common test modes | `--output-dir` (default `test_iq/vectors/common/`) |
| `python/grident/generate_test_iq.py` | Single capture by `--mode-id` or `--profile` | `--output` path |
| `python/grident/generate_docs.py` | Regenerate IQ + docs + plots + run tests | `test_iq/`, fixtures, `docs/` |

### Key generation functions

| Function | File | Role |
|---|---|---|
| `write_mode_capture()` | `generate_common_modes.py` | Write one mode `.cf32` + `.json` |
| `build_burst()` | `generate_test_iq.py` | Build one preamble IQ burst |
| `ModulationProfile.modulate_preamble()` | `modulation/profile.py` | Sync + Golay + guard silence |
| `ModulationProfile.modulate_bits()` | `modulation/profile.py` | Raw bit stream to IQ |
| `encode_preamble()` | `preamble.py` | 12-bit field to 24-bit Golay codeword |
| `get_profile_for_mode()` | `modulation/registry.py` | Mode ID to air-interface profile |
| `COMMON_MODES` | `common_modes.py` | Mode list for regression (20, 30, 40, 104, 108, 110, 158, 159) |

### IQ output locations

| Path | Used by |
|---|---|
| `test_iq/vectors/common/mode_XXX.cf32` | Dev vectors, docs generator |
| `python/tests/fixtures/common_modes/mode_XXX.cf32` | `unittest` regression (committed) |

---

## Decode pipeline

```
.cf32 file + .json sidecar
        │
        ▼
decode_iq_file()                iq_decode.py
        │
        ▼
ModulationProfile.decode_signal() profile.py
        ├── correlate_sync()      fsk.py / psk.py / rtty.py
        ├── demodulate_*()        profile-specific
        └── decode_preamble()       preamble.py (Golay decode)
        │
        ▼
IqDecodeResult
```

| Function | File | Role |
|---|---|---|
| `decode_iq_file()` | `iq_decode.py` | Load `.cf32`, pick profile from metadata |
| `decode_iq_signal()` | `iq_decode.py` | Decode in-memory `IqSamples` |
| `load_iq_metadata()` | `iq_decode.py` | Read sidecar JSON |
| `main()` | `apps/grident_iq_test.py` | CLI wrapper around `decode_iq_file()` |

---

## Python modules

### Core

| Module | Key symbols |
|---|---|
| `preamble.py` | `PreambleField`, `pack_field`, `unpack_field`, `encode_preamble`, `decode_preamble`, `codeword_to_bits_msb_first` |
| `golay.py` | `encode_golay24`, `decode_golay24` |
| `iq_samples.py` | `IqSamples`, `read_cf32`, `write_cf32`, `add_awgn`, `vdot` |
| `common_modes.py` | `CommonMode`, `COMMON_MODES`, `COMMON_MODE_BY_ID` |

### Modulation

| Module | Key symbols |
|---|---|
| `modulation/registry.py` | `PROFILE_BY_MODE_ID`, `get_profile`, `get_profile_for_mode`, profile constants (`NFM_125_4800`, `PSK31_3125`, …) |
| `modulation/profile.py` | `ModulationProfile`, `GUARD_SILENCE_SEC`, `modulate_preamble`, `decode_signal` |
| `modulation/fsk.py` | `modulate_cpfsk`, `demodulate_cpfsk`, `correlate_sync`, `bits_to_symbols` |
| `modulation/psk.py` | `modulate_bpsk`, `demodulate_bpsk`, `correlate_sync` |
| `modulation/rtty.py` | `modulate_fsk2`, `demodulate_fsk2`, `correlate_sync` |
| `modulation/squelch.py` | `ctcss_overlay`, `dcs_overlay` |

### Documentation plots

| Module | Key symbols |
|---|---|
| `docs_plots.py` | `render_waterfall`, `render_waterfall_context`, `render_time_plot`, `render_spectrum`, `stft_power_db` |
| `generate_docs.py` | `regenerate_iq`, `decode_results`, `write_modulation_doc`, `write_test_results` |

---

## C++ core (`blocklib/grident/`)

Built with Meson (`meson compile -C build`) and linked into the GR4 plugin (`cmake -B build-gr4`).

| File | Key symbols |
|---|---|
| `lib/golay24_12.cc` | `golay24_12::encode`, `golay24_12::decode` |
| `lib/preamble_field.cc` | `pack_preamble_field`, `unpack_preamble_field` |
| `lib/preamble_codec.cc` | `encode_preamble`, `decode_preamble`, bit/codeword helpers |
| `lib/mode_table.cc` | `lookup_mode`, `mode_name`, `k_modes[]` |
| `include/gnuradio/grident/*.h` | Public C++ API headers |

---

## Tests

### Run all Python tests

```bash
PYTHONPATH=python python3 -m unittest discover -s python/tests -v
```

### Python tests (`python/tests/`)

| File | Test class / function | What it checks |
|---|---|---|
| `test_grident.py` | `GolayTests.test_round_trip` | Python Golay encode/decode |
| | `GolayTests.test_single_bit_correction` | Single-bit error correction |
| | `PreambleTests.test_field_pack` | 12-bit field pack/unpack |
| | `PreambleTests.test_preamble_round_trip` | Full preamble encode/decode |
| | `MesonTests.test_meson_unit_tests` | Runs C++ Meson test suite |
| | `IqRoundtripTests.test_generated_iq` | Single IQ generate + decode |
| `test_common_modes.py` | `ensure_fixtures()` | Regenerates fixture `.cf32` files |
| | `CommonModeIqTests.test_fixture_manifest` | Fixture files exist, metadata |
| | `test_real_modulation_profile_per_mode` | Profile name per mode ID |
| | `test_wrong_profile_does_not_decode` | C4FM vs NFM rejection |
| | `test_roundtrip_each_mode` | Golay + mode ID decode per fixture |
| | `test_cross_identification_matrix` | 8x8 unique identification |
| | `test_metadata_matches_decode` | JSON sidecar vs decode result |
| | `test_cli_rejects_wrong_expectation` | `grident_iq_test.py` exit code |
| | `test_codewords_match_mode_table` | Codeword consistency |

### C++ tests (`blocklib/grident/test/`)

| File | Role |
|---|---|
| `test_golay.cc` | Golay(24,12) encode/decode, mode table lookup |
| `test_preamble_field.cc` | Field pack/unpack |
| `test_registry.cc` | GNU Radio 4 block registry smoke test |

Run C++ tests only:

```bash
meson test -C build --verbose
```

---

## Mode ID to profile map (quick reference)

| Mode ID | Profile | Modulation module |
|---:|---|---|
| 20, 110 | `nfm_125_4800` | `fsk.py` |
| 30 | `nfm_125_ctcss_4800` | `fsk.py` + `squelch.py` |
| 40 | `nfm_125_dcs_4800` | `fsk.py` + `squelch.py` |
| 104 | `c4fm_4800` | `fsk.py` |
| 108 | `dpmr_4800` | `fsk.py` |
| 158 | `psk31_3125` | `psk.py` |
| 159 | `rtty_50` | `rtty.py` |

Defined in `python/grident/modulation/registry.py` (`PROFILE_BY_MODE_ID`).

---

## Common debug commands

```bash
# Generate all common-mode IQ files
PYTHONPATH=python python3 python/grident/generate_common_modes.py

# Generate one mode
PYTHONPATH=python python3 python/grident/generate_test_iq.py \
  --mode-id 158 --output /tmp/mode_158.cf32

# Decode a capture
PYTHONPATH=python python3 apps/grident_iq_test.py \
  --input python/tests/fixtures/common_modes/mode_020.cf32

# Regenerate docs, plots, and test-results.md
PYTHONPATH=python python3 python/grident/generate_docs.py
```
