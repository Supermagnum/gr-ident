# Normative Sync Sequences

Synchronization bit patterns are transmitted **MSB-first** immediately before the
Golay(24,12) preamble codeword(s). Implementations must match these patterns exactly.

Canonical source: [`python/grident/sync_sequences.py`](../python/grident/sync_sequences.py)

## 16-bit sequences

### `sync_nfm` — NFM 12.5 kHz family (`nfm_125_*`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0x5BCA` |
| Binary (MSB first) | `0101101111001010` |
| Profiles | `nfm_125_4800`, `nfm_125_ctcss_4800`, `nfm_125_dcs_4800` |

### `sync_nxdn` — NXDN (`nxdn_4800`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0x4D63` |
| Binary (MSB first) | `0100110101100011` |

### `sync_m17` — M17 (`m17_4800`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0x3ACE` |
| Binary (MSB first) | `0011101011001110` |

### `sync_dstar` — D-STAR test vectors (`dstar_4800`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0x98E5` |
| Binary (MSB first) | `1001100011100101` |

### `sync_psk31` — PSK31 (`psk31_3125`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0xB274` |
| Binary (MSB first) | `1011001001110100` |

### `sync_rtty` — RTTY (`rtty_50`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0x69CD` |
| Binary (MSB first) | `0110100111001101` |

### `sync_ax25` — AX.25 Bell 202 (`ax25_1200`)

| Property | Value |
|---|---|
| Length | 16 bits |
| Hex | `0x6E4B` |
| Binary (MSB first) | `0110111001001011` |

## 24-bit sequences

### `sync_c4fm` — C4FM / Fusion (`c4fm_4800`)

| Property | Value |
|---|---|
| Length | 24 bits |
| Hex | `0xF9AD96` |
| Binary (MSB first) | `111110011010110110010110` |

### `sync_dpmr` — dPMR (`dpmr_4800`)

| Property | Value |
|---|---|
| Length | 24 bits |
| Hex | `0xA671AC` |
| Binary (MSB first) | `101001100111000110101100` |

### `sync_dmr` — DMR family (`dmr_4800`)

| Property | Value |
|---|---|
| Length | 24 bits |
| Hex | `0xB3969A` |
| Binary (MSB first) | `101100111001011010011010` |

## Mode ID to profile mapping

Assigned profiles are listed in [`python/grident/modulation/registry.py`](../python/grident/modulation/registry.py)
(`PROFILE_BY_MODE_ID`). Test captures cover eight common modes; additional mode IDs
reuse the profiles above for specification and implementation reference.
