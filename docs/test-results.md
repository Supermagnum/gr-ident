# Test Results

Generated: 2026-05-27 21:19:42 UTC

**Overall:** PASS (python exit 0, GR4 ctest exit 0)

## Python unit tests

```text
test_cli_rejects_wrong_expectation (test_common_modes.CommonModeIqTests.test_cli_rejects_wrong_expectation) ... ok
test_codewords_match_mode_table (test_common_modes.CommonModeIqTests.test_codewords_match_mode_table) ... ok
test_cross_identification_matrix (test_common_modes.CommonModeIqTests.test_cross_identification_matrix) ... ok
test_fixture_manifest (test_common_modes.CommonModeIqTests.test_fixture_manifest) ... ok
test_metadata_matches_decode (test_common_modes.CommonModeIqTests.test_metadata_matches_decode) ... ok
test_real_modulation_profile_per_mode (test_common_modes.CommonModeIqTests.test_real_modulation_profile_per_mode) ... ok
test_roundtrip_each_mode (test_common_modes.CommonModeIqTests.test_roundtrip_each_mode) ... ok
test_wrong_profile_does_not_decode (test_common_modes.CommonModeIqTests.test_wrong_profile_does_not_decode) ... ok
test_ptt_preamble_burst (test_gr4_flowgraphs.Gr4PttZmqSmokeTest.test_ptt_preamble_burst) ... ok
test_mode_110_fixture (test_gr4_flowgraphs.Gr4ReceiveFlowgraphTest.test_mode_110_fixture) ... ok
test_receive_yaml (test_gr4_flowgraphs.Gr4YamlFlowgraphTest.test_receive_yaml) ... skipped 'YAML loader requires scheduler-wrapped graph; use grident_receive_flowgraph'
test_round_trip (test_grident.GolayTests.test_round_trip) ... ok
test_single_bit_correction (test_grident.GolayTests.test_single_bit_correction) ... ok
test_generated_iq (test_grident.IqRoundtripTests.test_generated_iq) ... ok
test_meson_unit_tests (test_grident.MesonTests.test_meson_unit_tests) ... ok
test_field_pack (test_grident.PreambleTests.test_field_pack) ... ok
test_preamble_round_trip (test_grident.PreambleTests.test_preamble_round_trip) ... ok
test_assigned_mode_count (test_sync_metadata.ExtendedProfileTests.test_assigned_mode_count) ... ok
test_ax25_mode (test_sync_metadata.ExtendedProfileTests.test_ax25_mode) ... ok
test_dmr_mode (test_sync_metadata.ExtendedProfileTests.test_dmr_mode) ... ok
test_callsign_nibble (test_sync_metadata.MetadataFieldTests.test_callsign_nibble) ... ok
test_golay_round_trip (test_sync_metadata.MetadataFieldTests.test_golay_round_trip) ... ok
test_pack_round_trip (test_sync_metadata.MetadataFieldTests.test_pack_round_trip) ... ok
test_modulate_with_metadata (test_sync_metadata.MetadataPreambleAirTests.test_modulate_with_metadata) ... ok
test_legacy_strict_reserved (test_sync_metadata.PreambleBit9Tests.test_legacy_strict_reserved) ... ok
test_metadata_present_flag (test_sync_metadata.PreambleBit9Tests.test_metadata_present_flag) ... ok
test_primary_only_still_works (test_sync_metadata.PreambleBit9Tests.test_primary_only_still_works) ... ok
test_all_sequences_unique_names (test_sync_metadata.SyncSequenceTests.test_all_sequences_unique_names) ... ok
test_nfm_bits_match_doc (test_sync_metadata.SyncSequenceTests.test_nfm_bits_match_doc) ... ok
test_format_roundtrip (test_tx_control.TestTxControl.test_format_roundtrip) ... ok
test_json (test_tx_control.TestTxControl.test_json) ... ok
test_linht_pmt (test_tx_control.TestTxControl.test_linht_pmt) ... ok
test_plain_on_off (test_tx_control.TestTxControl.test_plain_on_off) ... ok

----------------------------------------------------------------------
Ran 33 tests in 152.075s

OK (skipped=1)
```

## GR4 smoke tests (ctest)

```text
Internal ctest changing into directory: /mnt/2e9a1e9f-2097-408c-ab9a-a01b32f11d28/github-projects/gr-ident/build-gr4
Test project /mnt/2e9a1e9f-2097-408c-ab9a-a01b32f11d28/github-projects/gr-ident/build-gr4
    Start 1: grident_registry
1/3 Test #1: grident_registry .................   Passed    0.02 sec
    Start 2: grident_receive_flowgraph
2/3 Test #2: grident_receive_flowgraph ........   Passed    0.23 sec
    Start 3: grident_ptt_zmq_smoke
3/3 Test #3: grident_ptt_zmq_smoke ............   Passed   12.13 sec

100% tests passed, 0 tests failed out of 3

Total Test time (real) =  12.38 sec
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
