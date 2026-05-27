# Test Results

Generated: 2026-05-27 18:48:25 UTC

**Overall:** PASS (exit code 0)

## Unit Test Log

```text
Tests skipped.
```

## Per-Mode IQ Roundtrip

| Mode ID | Name | Profile | Modulation | Samples | Decode | Roundtrip |
|---:|---|---|---|---:|---|---|
| 20 | NFM 12.5 kHz | `nfm_125_4800` | cpfsk4 @ 4800 | 96200 | OK | OK |
| 30 | NFM 12.5 kHz + CTCSS | `nfm_125_ctcss_4800` | cpfsk4 @ 4800 | 101000 | OK | OK |
| 40 | NFM 12.5 kHz + DCS | `nfm_125_dcs_4800` | cpfsk4 @ 4800 | 101000 | OK | OK |
| 104 | C4FM / Fusion | `c4fm_4800` | cpfsk4 @ 4800 | 96240 | OK | OK |
| 108 | dPMR | `dpmr_4800` | cpfsk4 @ 4800 | 96240 | OK | OK |
| 110 | EchoLink | `nfm_125_4800` | cpfsk4 @ 4800 | 96200 | OK | OK |
| 158 | PSK31 | `psk31_3125` | bpsk @ 31.25 | 157440 | OK | OK |
| 159 | RTTY | `rtty_50` | fsk2 @ 50 | 134400 | OK | OK |

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
