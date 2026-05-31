# gr-ident Validation Report (example)

Generated: 2026-05-27T12:00:00Z
radio-modulation-validator: not available

## Summary

| Layer | Checked | Passed | Failed | Skipped |
|---|---|---|---|---|
| Preamble (Golay roundtrip) | 8 | 8 | 0 | 0 |
| Signal (rmv classifier) | 8 | 0 | 0 | 8 |

## Per-mode results

| Mode ID | Name | Preamble | Signal family | Signal order | Notes |
|---|---|---|---|---|---|
| 20 | NFM 12.5 kHz | pass | | | radio-modulation-validator not found |
| 30 | NFM 12.5 kHz + CTCSS | pass | | | radio-modulation-validator not found |
| 40 | NFM 12.5 kHz + DCS | pass | | | radio-modulation-validator not found |
| 104 | C4FM / Fusion | pass | | | radio-modulation-validator not found |
| 108 | dPMR | pass | | | radio-modulation-validator not found |
| 110 | EchoLink | pass | | | radio-modulation-validator not found |
| 158 | PSK31 | pass | | | radio-modulation-validator not found |
| 159 | RTTY | pass | | | radio-modulation-validator not found |

## Known ambiguities

(none triggered in this run)

## Methodology

Preamble validation: Golay(24,12) encode, decode roundtrip, field
extraction, and comparison against committed fixture codewords.

Signal validation: IQ test vectors classified by radio-modulation-validator
family and order classifiers (ONNX, 91.84% family accuracy, 70.48% order
accuracy on 43 classes). Reference data generated independently from
gr-ident blocks.

When rmv is installed with ONNX models, signal rows show predictions such as:

| Mode ID | Name | Preamble | Signal family | Signal order | Notes |
|---|---|---|---|---|---|
| 20 | NFM 12.5 kHz | pass | FM pass (0.94) | NBFM_25 pass (0.87) | |
| 100 | DMR | pass | FSK pass (1.00) | DMR pass (1.00) | |
| 300 | Sleipnir | pass | custom pass (1.00) | sleipnir_8qpsk pass | plugin |
