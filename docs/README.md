# gr-ident Documentation

Generated test documentation for gr-ident modulation profiles and IQ captures.

**Test status:** PASS

## Contents

- [Modulation captures and waterfall plots](modulation-captures.md)
- [Test results](test-results.md)
- [Code chart](codechart.md)

## Tested modes

- Mode 20: NFM 12.5 kHz (`nfm_125_4800`)
- Mode 30: NFM 12.5 kHz + CTCSS (`nfm_125_ctcss_4800`)
- Mode 40: NFM 12.5 kHz + DCS (`nfm_125_dcs_4800`)
- Mode 104: C4FM / Fusion (`c4fm_4800`)
- Mode 108: dPMR (`dpmr_4800`)
- Mode 110: EchoLink (`nfm_125_4800`)
- Mode 158: PSK31 (`psk31_3125`)
- Mode 159: RTTY (`rtty_50`)

## IQ vectors

Regenerated captures live in:

- `test_iq/vectors/common/` — development vectors
- `python/tests/fixtures/common_modes/` — regression fixtures

## Plot parameters

| Parameter | Value |
|---|---|
| Sample rate | 48000 Hz |
| Waterfall width | 14 kHz (+/-7 kHz) |
| Waterfall (detail) | Zoomed to modulated body; fine STFT for short bursts |
| Waterfall (context) | Full capture with 1 s guard silence each side |
| STFT (detail) | Adaptive: nfft 256-2048, hop 4-128 by body length |
| Image height | 480 px (time axis resampled) |
| Power range | -55 to +5 dB (relative) |

## Regenerate

```bash
PYTHONPATH=python python3 python/grident/generate_docs.py
```

Requires ImageMagick (`convert`) for PNG export.
