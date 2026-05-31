# gr-ident, a Radio Mode Identification Preamble for Gnuradio — Specification

> **AI DISCLAIMER**: This specification was developed with the assistance of AI (Claude by Anthropic).
> GNU Radio 4.x is designed with AI-assisted development in mind, making it particularly suitable
> for implementing this specification. The specification has not been reviewed by professional
> engineers. Use at your own risk.

---

## Table of Contents

- [Overview](#overview)
- [Documentation](#documentation)
  - [Documentation index](docs/README.md)
  - [Test results](docs/test-results.md)
  - [Modulation captures](docs/modulation-captures.md)
  - [Code chart](docs/codechart.md)
  - [Sync sequences](docs/sync-sequences.md)
  - [Experimental mode registry](docs/experimental-mode-registry.md)
  - [ZeroMQ protocol](docs/zeromq-protocol.md)
  - [Gateway integration (VoIP + ZMQ + gr-linux-crypto)](docs/gateway-integration.md)
  - [radio-modulation-validator integration](docs/rmv-integration.md)
- [Design Goals](#design-goals)
  - [Preamble Structure](#preamble-structure)
  - [Modulation Profiles](#modulation-profiles)
- [Golay(24,12) Protection](#golay2412-protection)
- [12-Bit Field Layout](#12-bit-field-layout)
- [Mode ID Table](#mode-id-table)
  - [Reserved](#reserved)
  - [Analog Modes](#analog-modes)
  - [Digital Modes](#digital-modes)
  - [Image and Television Modes](#image-and-television-modes)
  - [Satellite Modes](#satellite-modes)
  - [Experimental Range](#experimental-range)
- [Receiver Behavior](#receiver-behavior)
- [Interaction with LDPC](#interaction-with-ldpc)
- [Security Integration — gr-linux-crypto](#security-integration--gr-linux-crypto)
- [GNU Radio 4.x OOT module](#gnu-radio-4x-oot-module)
- [Future Work](#future-work)
- [License](#license)

---

## Overview

This document specifies **gr-ident**, an open standard for a lightweight radio mode
identification preamble for use in amateur and experimental software-defined radio systems.
The specification is published freely, may be implemented by anyone without licensing
requirements, and is intended for open, interoperable use across receivers, transmitters,
and software-defined radio tooling.

The preamble allows a receiver to identify the incoming signal mode — analog or digital —
before committing to a demodulator, without relying on statistical signal classification
methods such as machine learning.

The preamble is self-contained, protected by forward error correction, and is entirely
transparent to any downstream LDPC decoder. It is designed to be decodable on modest
CPU hardware with no GPU requirement.

---

## Documentation

Generated test documentation, IQ capture details, waterfall plots, and regression results:

- [docs/README.md](docs/README.md) — documentation index and plot parameters
- [docs/test-results.md](docs/test-results.md) — unit test log and IQ roundtrip matrix
- [docs/modulation-captures.md](docs/modulation-captures.md) — per-mode air interfaces, capture durations, and spectrograms
- [docs/codechart.md](docs/codechart.md) — code and test function map (debug reference)
- [blocklib/grident/blocks/README.md](blocklib/grident/blocks/README.md) — GNU Radio 4.x block build
- [TESTING.md](TESTING.md) — tester onboarding and smoke tests
- [docs/zeromq-protocol.md](docs/zeromq-protocol.md) — LinHT and gr-ident ZeroMQ wire formats and mode examples
- [docs/gateway-integration.md](docs/gateway-integration.md) — VoIP gateway adapters, ZeroMQ, gr-linux-crypto
- [docs/rmv-integration.md](docs/rmv-integration.md) — two-layer IQ validation via radio-modulation-validator
- [apps/flowgraphs/zmq-distributed-demo.md](apps/flowgraphs/zmq-distributed-demo.md) — ZeroMQ distributed edges

Regenerate with:

```bash
PYTHONPATH=python python3 python/grident/generate_docs.py
```

---

## Design Goals

- Identify the incoming signal mode before demodulation begins
- Distinguish analog from digital signals at the earliest possible point
- Protect the mode identifier with FEC decodable at low SNR on any CPU
- Never interfere with or confuse downstream LDPC decoders
- Support up to 500 assigned modes with room for growth
- Remain simple enough to implement in GNU Radio 4.x without specialist hardware
- Carry minimal but useful metadata alongside the mode ID

---

## Preamble Structure

The preamble consists of a single Golay(24,12) codeword transmitted before the main
frame payload. It occupies a fixed number of symbols at the start of each transmission
and is consumed entirely before the downstream decoder sees any data.

```
+------------------+-----------------------------+
|  PREAMBLE        |  MAIN FRAME PAYLOAD         |
|  24 bits         |  (LDPC or other FEC)        |
|  Golay(24,12)    |  Decoder starts here only   |
+------------------+-----------------------------+
```

The boundary between the preamble and the main frame is fixed and defined by the
modulation in use. The downstream decoder is started only after the preamble has been
fully consumed and validated.

A known synchronization sequence (correlatable without carrier lock or symbol timing
recovery) must precede the preamble to allow detection at negative SNR. Sync sequences
and physical layer parameters are **modulation-specific** and defined in
[Modulation Profiles](#modulation-profiles).

---

## Modulation Profiles

Each mode uses a defined air interface for transmitting the sync sequence and 24-bit
Golay-protected preamble. IQ test vectors and conforming implementations must use the
profile assigned to that mode ID.

Common physical layer parameters for narrowband digital profiles:

| Parameter | Value | Reference |
|---|---|---|
| Symbol rate | 4800 sym/s | ETSI TS 102 490, Yaesu C4FM |
| 4-FSK deviations | ±648 Hz, ±1944 Hz | ETSI TS 102 490-1 |
| Sample rate (test vectors) | 48000 Hz | 10 samples/symbol |

### Profile: `nfm_125_4800`

Used by **NFM 12.5 kHz** (mode 20) and **EchoLink** (mode 110, FM gateway path).

| Parameter | Value | Reference |
|---|---|---|
| Channel | 12.5 kHz NFM | ETSI EN 300 113 |
| Data burst | 4800 sym/s CPFSK 4-FSK | ETSI TS 102 490 deviations |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_nfm)) |

### Profile: `nfm_125_ctcss_4800`

Used by **NFM 12.5 kHz + CTCSS** (mode 30).

| Parameter | Value | Reference |
|---|---|---|
| Base | `nfm_125_4800` | |
| CTCSS tone | 88.5 Hz | EIA/TIA-603 |
| CTCSS deviation | 500 Hz | Typical repeater practice |
| Preamble | Clean 4-FSK burst (no CTCSS on preamble) | gr-ident rule |
| Payload | CTCSS-only carrier for remainder of 3 s body | Simulates voice segment |

### Profile: `nfm_125_dcs_4800`

Used by **NFM 12.5 kHz + DCS** (mode 40).

| Parameter | Value | Reference |
|---|---|---|
| Base | `nfm_125_4800` | |
| DCS rate | 134.4 bit/s | ETSI TS 103 236 |
| DCS shift | ±134 Hz | ETSI TS 103 236 |
| Test code | 023 | Standard test codeword |
| Preamble | Clean 4-FSK burst (no DCS on preamble) | gr-ident rule |
| Payload | DCS-only carrier for remainder of 3 s body | Simulates voice segment |

### Profile: `c4fm_4800`

Used by **C4FM / Fusion** (mode 104).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | C4FM 4-FSK | Yaesu System Fusion |
| Symbol rate | 4800 sym/s | |
| Sync | 24-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_c4fm)) |

### Profile: `dpmr_4800`

Used by **dPMR** (mode 108).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | 4-FSK | ETSI TS 102 490-1 |
| Symbol rate | 4800 sym/s | |
| Sync | 24-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_dpmr)) |

### Profile: `psk31_3125`

Used by **PSK31** (mode 158).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | BPSK | PSK31 amateur digital mode |
| Symbol rate | 31.25 baud | PSK31 standard |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_psk31)) |

### Profile: `rtty_50`

Used by **RTTY** (mode 159).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | 2-FSK | ITA2 radioteletype |
| Symbol rate | 50 baud | Common amateur RTTY rate |
| Frequency shift | 170 Hz (mark +85 Hz, space -85 Hz) | ITA2 audio shift |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_rtty)) |

### Profile: `dmr_4800`

Used by **DMR** modes 100-102, 106, and 109 (test-vector placeholder).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | 4-FSK | ETSI TS 102 361 |
| Symbol rate | 4800 sym/s | |
| Sync | 24-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_dmr)) |

### Profile: `nxdn_4800`

Used by **NXDN** (mode 107).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | 4-FSK | NXDN common air interface |
| Symbol rate | 4800 sym/s | |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_nxdn)) |

### Profile: `m17_4800`

Used by **M17** modes 120 and 121.

| Parameter | Value | Reference |
|---|---|---|
| Modulation | 4-FSK | M17 open digital voice |
| Symbol rate | 4800 sym/s | |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_m17)) |

### Profile: `dstar_4800`

Used by **D-STAR** (mode 103) and **D-STAR Reflector** (mode 115). Test vectors use
4-FSK at 4800 sym/s as a correlatable placeholder for gateway paths.

| Parameter | Value | Reference |
|---|---|---|
| Modulation | 4-FSK (test vectors) | D-STAR digital voice |
| Symbol rate | 4800 sym/s | |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_dstar)) |

### Profile: `ax25_1200`

Used by **AX.25** (mode 150) and **APRS** (mode 151).

| Parameter | Value | Reference |
|---|---|---|
| Modulation | Bell 202 AFSK | AX.25 amateur packet |
| Symbol rate | 1200 baud | |
| Sync | 16-bit sequence | gr-ident assigned (see [Sync Sequences](docs/sync-sequences.md#sync_ax25)) |

Mode ID to profile mapping for assigned modes is implemented in
`python/grident/modulation/registry.py`.

The gr-ident preamble is always a clean data burst at the start of a
transmission. For NFM modes with CTCSS or DCS, test vectors append a
squelch-tone payload after the preamble for the remainder of the **3 second**
modulated body; decoders must not apply CTCSS/DCS compensation to the preamble
symbols themselves.

All IQ test vectors use this layout:

```
[ 1 s silence ] [ 3 s modulated body ] [ 1 s silence ]
```

The modulated body begins with the sync + Golay preamble burst. The remainder
is profile-specific payload (CTCSS/DCS tone, idle carrier, RTTY mark, and so on).

---

## Golay(24,12) Protection

The 12 data bits of the preamble field are encoded using a Golay(24,12) perfect binary
linear code, producing 24 bits for transmission.

Properties:

- **Data bits**: 12
- **Encoded bits**: 24
- **Minimum Hamming distance**: 8
- **Error correction**: up to 3 bit errors per codeword
- **Error detection**: up to 7 bit errors per codeword
- **Decoding complexity**: trivial on any CPU, microsecond latency
- **No interaction** with downstream LDPC or convolutional decoders

The generator polynomial and encoding/decoding procedure follow the standard
Golay(24,12) definition as used in, for example, the M17 protocol LICH channel.

---

## 12-Bit Field Layout

The 12 data bits protected by the Golay codeword are allocated as follows:

```
Bit 11        Bit 10        Bit 9              Bits 8–0
+-----------+-----------+------------------+------------------+
| Analog /  | Encrypted /| Metadata present | Mode ID          |
| Digital   | Open       | (optional ext.)  | (9 bits, 0–511)  |
+-----------+-----------+------------------+------------------+
```

| Field | Bits | Description |
|---|---|---|
| Mode ID | 9 (bits 0–8) | Identifies the specific mode (0–511) |
| Metadata present | 1 (bit 9) | 0 = primary preamble only; 1 = secondary metadata codeword follows on air |
| Encrypted / Open | 1 (bit 10) | 0 = open / unencrypted, 1 = encrypted content |
| Analog / Digital | 1 (bit 11) | 0 = analog mode, 1 = digital mode |

The **Analog / Digital flag** (bit 11) is the most significant bit, allowing a receiver
to make the analog/digital routing decision immediately from the MSB alone, without
needing to decode the full Mode ID. This is the minimum useful action a receiver can
take upon preamble detection.

The **Encrypted / Open flag** (bit 10) signals whether the payload content is encrypted.
Note that encryption may be subject to regulatory restrictions depending on jurisdiction
and frequency band. Users are responsible for compliance with applicable regulations.

---

## Optional Secondary Metadata Field

When bit 9 (**Metadata present**) is set in the primary preamble field, a second
Golay(24,12) codeword is transmitted immediately after the primary codeword (still
before the main payload). The on-air order is:

```
[ sync ] [ primary Golay 24 bits ] [ secondary Golay 24 bits ] [ payload ... ]
```

The 12 data bits of the secondary field are allocated as follows:

```
Bit 11–8       Bit 7–4        Bit 3–0
+-------------+-------------+--------------+
| Bandwidth   | Codec param | Callsign     |
| code        | (4 bits)    | nibble       |
+-------------+-------------+--------------+
```

| Field | Bits | Description |
|---|---|---|
| Bandwidth code | 4 (bits 11–8) | Channel bandwidth hint (see table below) |
| Codec param | 4 (bits 7–4) | Mode-specific sub-codec or rate index (0–15) |
| Callsign nibble | 4 (bits 3–0) | Upper four bits of CRC-16-CCITT of callsign (0 if none) |

| Bandwidth code | Meaning |
|---|---|
| 0 | Unspecified |
| 1 | 6.25 kHz |
| 2 | 8.33 kHz |
| 3 | 12.5 kHz |
| 4 | 20 kHz |
| 5 | 25 kHz |
| 6 | WFM / wide |
| 7–15 | Reserved |

Implementations: `python/grident/metadata_field.py`, `blocklib/grident/lib/metadata_field.cc`,
GNU Radio 4.x blocks `MetadataEncode` and `MetadataDecode`.

Receivers that do not implement the secondary field must still decode the primary
preamble when bit 9 = 0. When bit 9 = 1, conforming receivers should decode both
codewords before routing to the payload demodulator.

---

## Mode ID Table

### Reserved

| Mode ID | Hex | Description |
|---|---|---|
| 0 | 0x000 | Null / unassigned |
| 511 | 0x1FF | Test / loopback |

---

### Analog Modes
*(Bit 11 = 0)*

#### AM Variants

| Mode ID | Hex | Description |
|---|---|---|
| 1 | 0x001 | AM — Amplitude Modulation (standard) |
| 2 | 0x002 | AM-DSB — Double Sideband |
| 3 | 0x003 | AM-SSB — Single Sideband (generic) |
| 4 | 0x004 | USB — Upper Sideband |
| 5 | 0x005 | LSB — Lower Sideband |
| 6 | 0x006 | DSB-SC — Double Sideband Suppressed Carrier |

#### FM — Wide

| Mode ID | Hex | Description |
|---|---|---|
| 10 | 0x00A | WFM — Wideband FM, broadcast (200 kHz) |
| 11 | 0x00B | WFM Stereo — Wideband FM with stereo pilot |
| 12 | 0x00C | FM 25 kHz — Standard FM, 25 kHz channel spacing |
| 13 | 0x00D | FM 20 kHz — FM, 20 kHz channel spacing |

#### NFM — Narrowband FM, no tone squelch

| Mode ID | Hex | Description |
|---|---|---|
| 20 | 0x014 | NFM 12.5 kHz — Standard narrowband FM |
| 21 | 0x015 | NFM 8.33 kHz — Aviation narrowband FM |
| 22 | 0x016 | NFM 6.25 kHz — Very narrow FM |

#### NFM — with CTCSS (Continuous Tone-Coded Squelch System)

| Mode ID | Hex | Description |
|---|---|---|
| 30 | 0x01E | NFM 12.5 kHz + CTCSS |
| 31 | 0x01F | NFM 8.33 kHz + CTCSS |
| 32 | 0x020 | NFM 6.25 kHz + CTCSS |
| 33 | 0x021 | FM 25 kHz + CTCSS |
| 34 | 0x022 | FM 20 kHz + CTCSS |

#### NFM — with DCS (Digital-Coded Squelch)

| Mode ID | Hex | Description |
|---|---|---|
| 40 | 0x028 | NFM 12.5 kHz + DCS |
| 41 | 0x029 | NFM 8.33 kHz + DCS |
| 42 | 0x02A | NFM 6.25 kHz + DCS |
| 43 | 0x02B | FM 25 kHz + DCS |
| 44 | 0x02C | FM 20 kHz + DCS |

#### NFM — with CTCSS and DCS combined

| Mode ID | Hex | Description |
|---|---|---|
| 50 | 0x032 | NFM 12.5 kHz + CTCSS + DCS |
| 51 | 0x033 | NFM 8.33 kHz + CTCSS + DCS |
| 52 | 0x034 | NFM 6.25 kHz + CTCSS + DCS |

#### Other Analog

| Mode ID | Hex | Description |
|---|---|---|
| 60 | 0x03C | CW — Continuous Wave (Morse) |
| 61 | 0x03D | CW Narrow |
| 62 | 0x03E | NBAM — Narrowband AM |
| 63 | 0x03F | ECSS — Exalted Carrier Selectable Sideband |

---

### Digital Modes
*(Bit 11 = 1)*

#### Voice — Proprietary Codec

| Mode ID | Hex | Description |
|---|---|---|
| 100 | 0x064 | DMR — Digital Mobile Radio (ETSI TS 102 361) |
| 101 | 0x065 | DMR Tier II — Conventional |
| 102 | 0x066 | DMR Tier III — Trunked |
| 103 | 0x067 | D-STAR — Digital Smart Technologies for Amateur Radio |
| 104 | 0x068 | C4FM / Fusion — Yaesu System Fusion |
| 105 | 0x069 | P25 Phase 1 — APCO Project 25 (C4FM) |
| 106 | 0x06A | P25 Phase 2 — APCO Project 25 (TDMA) |
| 107 | 0x06B | NXDN — Icom / Kenwood narrowband digital |
| 108 | 0x06C | dPMR — Digital Private Mobile Radio |
| 109 | 0x06D | TETRA — Terrestrial Trunked Radio |

#### Voice Linking / VoIP Gateways

These mode IDs identify internet voice-linking services. They apply when the transmission
carries linked voice — for example after RF demodulation at a repeater or gateway, or when
routing voice through an IP bridge rather than a distinct over-the-air codec.

gr-ident **identifies** the link type on the RF preamble; it does **not** implement EchoLink,
IRLP, AllStar, Mumble, Wires-X, or D-STAR reflector protocols. A separate **gateway adapter**
bridges decoded mode IDs and audio/PTT to the VoIP stack. See
[Gateway integration reference](docs/gateway-integration.md) for ZeroMQ wiring and
[gr-linux-crypto](https://github.com/Supermagnum/gr-linux-crypto) hooks.

| Mode ID | Hex | Description | gr-ident RF profile (typical) | Gateway software |
|---:|---|---|---|---|
| 110 | 0x06E | EchoLink — node, conference, or repeater link | `nfm_125_4800` (test vector in repo) | [SvxLink](https://github.com/sm0svx/svxlink) |
| 111 | 0x06F | IRLP — Internet Radio Linking Project | Operator-defined (often NFM) | IRLP node |
| 112 | 0x070 | AllStar Link — Asterisk / app_rpt | Operator-defined (often NFM) | [ASL3](https://github.com/allstarlink/asl3) |
| 113 | 0x071 | Mumble — open-source VoIP (e.g. KA-Node) | Operator-defined | Mumble / [QRadioLink](https://qradiolink.org/) |
| 114 | 0x072 | Wires-X — Yaesu internet linking (link node) | `c4fm_4800` if digital RF | Yaesu Wires-X / MMDVM bridges |
| 115 | 0x073 | D-STAR Reflector — DCS / REF / XRF | D-STAR sync (`sync_dstar`) | [xlxd](https://github.com/n7tae/new-xlxd) / [urfd](https://github.com/n7tae/urfd) |

**Integration buses (gr-ident side):**

- **Receive:** subscribe to preamble JSON on `tcp://127.0.0.1:5560` (topic `grident`) after
  Golay decode; route on `mode_id`; if `encrypted` is true, invoke gr-linux-crypto before
  forwarding audio to the gateway ([ZeroMQ protocol](docs/zeromq-protocol.md)).
- **Transmit:** publish LinHT PMT `SOT`/`EOT` on `ipc:///tmp/ptt_msg` or gr-ident multipart
  PTT on `:5561`; GR `PreambleOnPtt` inserts the burst for the configured linking mode ID.

There are no mature GNU Radio OOT modules that speak these VoIP protocols end-to-end.
Documented patterns use **UDP/ALSA/USRP audio** between GNU Radio and SvxLink, AllStar, or
Mumble, with gr-ident handling RF identification only.

#### Voice — Open Codec

| Mode ID | Hex | Description |
|---|---|---|
| 120 | 0x078 | M17 — Open digital voice, Codec2 3200 |
| 121 | 0x079 | M17 — Codec2 1600 |
| 122 | 0x07A | FreeDV 700D |
| 123 | 0x07B | FreeDV 1600 |
| 124 | 0x07C | FreeDV 2020 |
| 125 | 0x07D | Codec2 2400 bps (raw, no framing) |
| 126 | 0x07E | Codec2 1200 bps (raw, no framing) |
| 127 | 0x07F | Opus (raw, no framing) |

#### Data / Packet

Slot-synchronized weak-signal modes (FT8, FT4, JS8Call, and similar) are intentionally
omitted. Their fixed transmit windows leave no room for a gr-ident preamble without
breaking protocol timing.

| Mode ID | Hex | Description |
|---|---|---|
| 150 | 0x096 | AX.25 — Amateur packet radio |
| 151 | 0x097 | APRS — Automatic Packet Reporting System |
| 152 | 0x098 | VARA HF |
| 153 | 0x099 | VARA FM |
| 154 | 0x09A | Winlink |
| 158 | 0x09E | PSK31 |
| 159 | 0x09F | RTTY — Radioteletype |

#### Broadband / Multi-carrier

| Mode ID | Hex | Description |
|---|---|---|
| 180 | 0x0B4 | OFDM — Generic OFDM (parameters in metadata) |
| 181 | 0x0B5 | COFDM — Coded OFDM |

---

### Image and Television Modes
*(Bit 11 = 1)*

#### SSTV — Slow Scan Television (Analog Image)

| Mode ID | Hex | Description |
|---|---|---|
| 210 | 0x0D2 | SSTV — Martin M1 |
| 211 | 0x0D3 | SSTV — Martin M2 |
| 212 | 0x0D4 | SSTV — Scottie S1 |
| 213 | 0x0D5 | SSTV — Scottie S2 |
| 214 | 0x0D6 | SSTV — Scottie DX |
| 215 | 0x0D7 | SSTV — Robot 36 |
| 216 | 0x0D8 | SSTV — Robot 72 |
| 217 | 0x0D9 | SSTV — PD 90 |
| 218 | 0x0DA | SSTV — PD 120 |
| 219 | 0x0DB | SSTV — PD 160 |
| 220 | 0x0DC | SSTV — PD 180 |
| 221 | 0x0DD | SSTV — PD 240 |
| 222 | 0x0DE | SSTV — Wraase SC2-120 |
| 223 | 0x0DF | SSTV — Wraase SC2-180 |

#### DSSTV / Digital Image

| Mode ID | Hex | Description |
|---|---|---|
| 230 | 0x0E6 | DSSTV — Digital Slow Scan Television |
| 231 | 0x0E7 | EasyPal — HF digital image (DRM-based) |
| 232 | 0x0E8 | FSSTV — Fast Scan ATV (narrowband digital) |
| 233 | 0x0E9 | FAX — HF radiofax / weatherfax |

#### ATV — Amateur Television

| Mode ID | Hex | Description |
|---|---|---|
| 240 | 0x0F0 | ATV — Analog amateur television (wideband) |
| 241 | 0x0F1 | ATV — NTSC |
| 242 | 0x0F2 | ATV — PAL |
| 243 | 0x0F3 | DATV — Digital ATV (DVB-S) |
| 244 | 0x0F4 | DATV — Digital ATV (DVB-S2) |
| 245 | 0x0F5 | DATV — Digital ATV (DVB-T) |

---

### Satellite Modes
*(Bit 11 = 1)*

Modes in this section cover amateur satellite **uplink** use — signals a station transmits
through a transponder. Receive-only downlinks (telemetry beacons, weather imaging,
navigation, ADS-B, and similar) are intentionally omitted; they cannot be influenced by
the transmitting station and are out of scope for gr-ident.

#### Satellite Voice and Data

| Mode ID | Hex | Description |
|---|---|---|
| 260 | 0x104 | Linear transponder — SSB/CW uplink/downlink |
| 261 | 0x105 | FM Satellite — Standard FM voice repeater |
| 262 | 0x106 | FM Satellite + CTCSS — FM with access tone |
| 264 | 0x108 | Es'hail-2 / QO-100 — NB transponder SSB |
| 265 | 0x109 | Es'hail-2 / QO-100 — WB transponder DATV |

---

### Experimental Range

Mode IDs 300–498 are reserved for experimental and user-defined modes. Assignments
within this range are recorded in the public
[experimental mode registry](docs/experimental-mode-registry.md)
(`registry/experimental-modes.json`).

| Range | Hex Range | Description |
|---|---|---|
| 300 | 0x12C | [Sleipnir](https://github.com/Supermagnum/gr-sleipnir) — 8-carrier QPSK digital voice (see [registry](docs/experimental-mode-registry.md)) |
| 301–498 | 0x12D–0x1F2 | Experimental / user-defined (unassigned) |
| 499 | 0x1F3 | Experimental range upper boundary marker |
| 500–510 | 0x1F4–0x1FE | Reserved for future standardization |
| 511 | 0x1FF | Test / loopback |

---

## Receiver Behavior

A conforming receiver should follow this decision tree upon preamble detection:

1. Detect synchronization sequence via correlation (modulation-specific)
2. Receive 24 preamble bits
3. Apply Golay(24,12) decoding and error correction
4. If decoding fails (more than 3 bit errors): fall back to squelch / discard
5. Extract bit 11 (Analog / Digital flag)
   - If 0: route to analog demodulator bank
   - If 1: route to digital demodulator bank
6. Extract bits 0–8 (Mode ID)
7. Look up Mode ID in local mode table
8. If mode is known: activate the corresponding demodulator
9. If mode is unknown: optionally alert user; do not pass noise to audio output
10. Extract bit 10 (Encrypted / Open flag) and handle accordingly
11. Pass remaining frame data to the downstream decoder (LDPC or other)

Step 5 alone — the analog/digital routing decision — is the minimum viable action.
Steps 6–9 provide full mode discrimination. A receiver may implement only step 5
and still provide useful behavior (no digital noise on analog audio output).

---

## Interaction with LDPC

The preamble is designed to be fully transparent to any downstream LDPC decoder.
The following rules ensure this:

- The preamble occupies a fixed, known number of bits (24) before the LDPC frame
- The LDPC decoder is not started until the preamble boundary has been passed
- The preamble uses Golay(24,12), which is entirely independent of LDPC
- No preamble bit pattern can form a valid LDPC codeword start, provided the
  synchronization sequence correctly delimits the boundary
- The preamble carries no data that the LDPC decoder needs to reference

Implementations must ensure the LDPC decoder input pointer starts at the correct
offset after the preamble. The preamble should be stripped from the bitstream before
it is passed to any downstream decoder.

---

## Security Integration — gr-linux-crypto

The preamble specification is designed to work alongside
[gr-linux-crypto](https://github.com/Supermagnum/gr-linux-crypto), an out-of-tree GNU Radio
module providing Linux-specific cryptographic infrastructure. When the **Encrypted / Open**
flag (bit 10) is set in the preamble, the payload that follows is encrypted and the receiver
must have access to the appropriate key material before demodulation is useful.

### How the Encrypted Flag Interacts with gr-linux-crypto

When bit 10 is set to 1:

1. The receiver identifies the mode from the Mode ID as normal
2. The receiver knows the payload is encrypted before attempting to decode it
3. Key material must be retrieved — from the Linux kernel keyring, a Nitrokey hardware
   security module, or an OpenPGP card — before the payload is passed to the demodulator
4. The decrypted payload is then passed to the appropriate demodulator for the identified mode

This allows a receiver to cleanly refuse to attempt demodulation of encrypted content
it has no key for, rather than producing noise or a failed decode.

### Supported Key Sources (via gr-linux-crypto)

| Key Source | Description |
|---|---|
| Linux kernel keyring | Keys stored securely in the kernel, accessed via `keyctl` |
| Nitrokey (password safe slot) | Keys stored on hardware token, never leave the device |
| OpenPGP card / Nitrokey Pro | Private key operations performed on-card |
| GnuPG agent | Keys managed by the GnuPG agent with pinentry PIN protection |

### Supported Cryptographic Operations

The following operations from gr-linux-crypto are relevant to encrypted preamble payloads:

| Operation | Algorithm | Use |
|---|---|---|
| Payload encryption | AES-256-GCM | Authenticated encryption of frame payload |
| Payload encryption | ChaCha20-Poly1305 | Battery-friendly authenticated encryption |
| Key agreement | Brainpool ECDH (P-256r1 / P-384r1 / P-512r1) | Session key establishment |
| Digital signature | Brainpool ECDSA | Callsign authentication; transmission signing |
| Digital signature | Ed25519 (via gr-nacl) | Open alternative signature scheme |
| Key derivation | HKDF (RFC 5869) | Deriving session keys from ECDH shared secret |
| Multi-recipient | Brainpool ECIES (up to 25 recipients) | Encrypting session key for multiple receivers |

### Regulatory Note

Amateur radio regulations in most jurisdictions prohibit encryption of on-air content.
The **Encrypted / Open** flag and associated gr-linux-crypto support are provided for:

- Experimental and research use on appropriate frequencies
- Digital signature authentication (bit 10 = 0; signatures do not encrypt content)
- Jurisdictions and frequency allocations where encryption is lawfully permitted

Users are solely responsible for ensuring their use complies with applicable regulations.
Setting bit 10 = 1 on amateur radio frequencies where encryption is prohibited is the
user's responsibility to avoid. The specification itself imposes no restriction.

### Digital Signatures Without Encryption

It is valid and useful to set bit 10 = 0 (open/unencrypted) while still using
gr-linux-crypto for **digital signatures**. In this case:

- The payload is transmitted in the clear and decodable by any receiver
- A signature frame (Ed25519 or Brainpool ECDSA, 64–72 bytes) is appended at the
  end of the transmission
- Receivers with signature verification capability can verify callsign authenticity
- Receivers without signature support simply ignore the trailing signature frame
- This provides progressive enhancement: authentication without breaking compatibility

This pattern follows the backward-compatible signature-at-end-of-transmission design
described in the gr-linux-crypto signing and verification documentation.

---

## GNU Radio 4.x OOT module

The reference out-of-tree module lives under `blocklib/grident/`. CMake builds:

| Plugin | Contents |
|---|---|
| `GrIdentBlocks` | Golay, preamble/metadata codec blocks, `PreambleOnPtt` (PTT-gated TX) |
| `GrIdentZmqBlocks` | ZeroMQ PUSH/PULL IQ edges, preamble JSON PUB, TX/PTT SUB (requires libzmq) |

Build:

```bash
cmake -B build-gr4 -DCMAKE_PREFIX_PATH=/opt/gnuradio4-gcc
cmake --build build-gr4
```

ZeroMQ blocks support distributed flowgraphs (IQ between hosts), publishing decoded
preamble fields as JSON on receive, and **TX/PTT control** on transmit (`ZmqTxControlSub`
into `PreambleOnPtt`). The default TX control profile matches the
[LinHT Handheld Transceiver](https://github.com/M17-Project/LinHT-utils) PMT `SOT`/`EOT`
messages on `ipc:///tmp/ptt_msg`; use `profile=grident` for standalone multipart JSON/text.
See [`docs/zeromq-protocol.md`](docs/zeromq-protocol.md) for wire formats and source references.
See [`apps/flowgraphs/zmq-distributed-demo.md`](apps/flowgraphs/zmq-distributed-demo.md).

IQ-level detection without GNU Radio remains in `python/grident/iq_decode.py` and
`blocklib/grident/lib/preamble_detect.cc`.

### IQ validation (radio-modulation-validator)

Committed IQ test vectors can be checked in two layers with `grident-validate`:

1. **Preamble** — Golay(24,12) encode/decode roundtrip against fixture codewords (no external deps)
2. **Signal** — optional classification via [radio-modulation-validator](https://github.com/Supermagnum/radio-modulation-validator) (rmv)

```bash
PYTHONPATH=python python3 apps/grident_validate.py --preamble-only
PYTHONPATH=python python3 apps/grident_validate.py \
  --fixtures python/tests/fixtures/common_modes/
```

If rmv is not installed, preamble checks still run and signal validation is skipped.
See [`docs/rmv-integration.md`](docs/rmv-integration.md) and [`TESTING.md`](TESTING.md).

---

## Future Work

- Additional modulation profiles and normative sync sequences for remaining mode IDs
- Hosted web UI for the experimental mode registry (JSON registry exists in-repo)
- GNU Radio 4.x streaming blocks for BPSK / 2-FSK profiles and full in-process flowgraph examples
- End-to-end gr-linux-crypto demo flowgraph (design reference:
  [`apps/flowgraphs/gr-linux-crypto-demo.md`](apps/flowgraphs/gr-linux-crypto-demo.md))
- Formal assignment of mode IDs for additional regional and emerging modes

---

## License

gr-ident is an **open standard**. This specification is released into the public domain.
No rights reserved. Implementers are free to use, modify, and distribute this specification
without restriction. Attribution is appreciated but not required.
