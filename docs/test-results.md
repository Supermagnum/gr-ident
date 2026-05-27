# Test Results

Generated: 2026-05-27 19:22:48 UTC

**Overall:** PASS (exit code 0)

## Unit Test Log

```text
test_cli_rejects_wrong_expectation (test_common_modes.CommonModeIqTests.test_cli_rejects_wrong_expectation) ... ok
test_codewords_match_mode_table (test_common_modes.CommonModeIqTests.test_codewords_match_mode_table) ... ok
test_cross_identification_matrix (test_common_modes.CommonModeIqTests.test_cross_identification_matrix) ... ok
test_fixture_manifest (test_common_modes.CommonModeIqTests.test_fixture_manifest) ... ok
test_metadata_matches_decode (test_common_modes.CommonModeIqTests.test_metadata_matches_decode) ... ok
test_real_modulation_profile_per_mode (test_common_modes.CommonModeIqTests.test_real_modulation_profile_per_mode) ... ok
test_roundtrip_each_mode (test_common_modes.CommonModeIqTests.test_roundtrip_each_mode) ... ok
test_wrong_profile_does_not_decode (test_common_modes.CommonModeIqTests.test_wrong_profile_does_not_decode) ... ok
test_round_trip (test_grident.GolayTests.test_round_trip) ... ok
test_single_bit_correction (test_grident.GolayTests.test_single_bit_correction) ... ok
test_generated_iq (test_grident.IqRoundtripTests.test_generated_iq) ... ok
test_meson_unit_tests (test_grident.MesonTests.test_meson_unit_tests) ... ok
test_field_pack (test_grident.PreambleTests.test_field_pack) ... ok
test_preamble_round_trip (test_grident.PreambleTests.test_preamble_round_trip) ... ok

----------------------------------------------------------------------
Ran 14 tests in 132.187s

OK
```

## Per-Mode IQ Roundtrip

| Mode ID | Name | Profile | Modulation | Samples | Decode | Roundtrip |
|---:|---|---|---|---:|---|---|
| 20 | NFM 12.5 kHz | `nfm_125_4800` | cpfsk4 @ 4800 | 240000 | OK | OK |
| 30 | NFM 12.5 kHz + CTCSS | `nfm_125_ctcss_4800` | cpfsk4 @ 4800 | 240000 | OK | OK |
| 40 | NFM 12.5 kHz + DCS | `nfm_125_dcs_4800` | cpfsk4 @ 4800 | 240000 | OK | OK |
| 104 | C4FM / Fusion | `c4fm_4800` | cpfsk4 @ 4800 | 240000 | OK | OK |
| 108 | dPMR | `dpmr_4800` | cpfsk4 @ 4800 | 240000 | OK | OK |
| 110 | EchoLink | `nfm_125_4800` | cpfsk4 @ 4800 | 240000 | OK | OK |
| 158 | PSK31 | `psk31_3125` | bpsk @ 31.25 | 240000 | OK | OK |
| 159 | RTTY | `rtty_50` | fsk2 @ 50 | 240000 | OK | OK |

## Codewords

| Mode ID | Expected codeword | Sync start |
|---:|---|---:|
| 20 | 0xcb4014 | 47997 |
| 30 | 0x5de01e | 47997 |
| 40 | 0x65a028 | 47997 |
| 104 | 0x314868 | 47997 |
| 108 | 0x92f86c | 47997 |
| 110 | 0xd5886e | 47997 |
| 158 | 0x3e289e | 48000 |
| 159 | 0xc1c89f | 48000 |
