# Experimental Mode ID Registry

Mode IDs **300-498** are reserved for experimental and user-defined modes. This file
is the public registry for assignments within that range.

## Registry file

Canonical data: [`registry/experimental-modes.json`](../registry/experimental-modes.json)

Each assignment entry uses this shape:

| Field | Type | Description |
|---|---|---|
| `mode_id` | integer | Assigned ID (300-498) |
| `holder` | string | Project or callsign requesting the ID |
| `name` | string | Short mode label |
| `profile` | string | gr-ident modulation profile name (if any) |
| `contact` | string | Email or project URL |
| `notes` | string | Optional description |

## Submitting an assignment

1. Choose an unused ID in 300-498 (check `assignments` in the JSON file).
2. Add an entry to `registry/experimental-modes.json`.
3. Open a pull request against this repository.

Implementers using experimental IDs locally without registering should document
assignments in their own project to avoid internal conflicts. Only entries merged
here are part of the public registry.

## Assigned modes

| Mode ID | Hex | Name | Holder | Profile | Reference |
|---:|---|---|---|---|---|
| 300 | 0x12C | Sleipnir | [Supermagnum/gr-sleipnir](https://github.com/Supermagnum/gr-sleipnir) | — | [GitHub](https://github.com/Supermagnum/gr-sleipnir) |

### Mode 300 — Sleipnir

Experimental GNU Radio-based digital voice mode for amateur narrowband FM (NFM) channel
spacing, using modern audio codecs for voice quality.

| Parameter | Value |
|---|---|
| Carriers | 8 parallel QPSK |
| Symbol rate | 900 baud per carrier (7,200 sym/s total) |
| Bits per symbol | 2 (QPSK) |
| Bandwidth per carrier | ~1,000–1,200 Hz (pulse shaped) |
| Carrier spacing | 1,300 Hz |

A gr-ident modulation profile for Sleipnir is not yet assigned in
`python/grident/modulation/registry.py`. Implementers should use mode ID **300** in the
primary preamble field (bit 11 = 1, digital).

## Related specification

See [Experimental Range](../README.md#experimental-range) in the main specification.
