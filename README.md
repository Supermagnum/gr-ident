# gr-ident, a Radio Mode Identification Preamble for Gnuradio — Specification

> **AI DISCLAIMER**: This specification was developed with the assistance of AI (Claude by Anthropic).
> GNU Radio 4.x is designed with AI-assisted development in mind, making it particularly suitable
> for implementing this specification. The specification has not been reviewed by professional
> engineers. Use at your own risk.

---

## Table of Contents

- [Overview](#overview)
- [Design Goals](#design-goals)
- [Preamble Structure](#preamble-structure)
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
- [Future Work](#future-work)
- [License](#license)

---

## Overview

This document specifies a lightweight radio mode identification preamble for use in amateur
and experimental software-defined radio systems. The preamble allows a receiver to identify
the incoming signal mode — analog or digital — before committing to a demodulator, without
relying on statistical signal classification methods such as machine learning.

The preamble is self-contained, protected by forward error correction, and is entirely
transparent to any downstream LDPC decoder. It is designed to be decodable on modest
CPU hardware with no GPU requirement.

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
recovery) should precede the preamble to allow detection at negative SNR. The design
of this sync sequence is modulation-specific and outside the scope of this document.

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
Bit 11        Bit 10        Bit 9         Bits 8–0
+-----------+-----------+-------------+------------------+
| Analog /  | Encrypted /| Reserved    | Mode ID          |
| Digital   | Open       | (set to 0)  | (9 bits, 0–511)  |
+-----------+-----------+-------------+------------------+
```

| Field | Bits | Description |
|---|---|---|
| Mode ID | 9 (bits 0–8) | Identifies the specific mode (0–511) |
| Reserved | 1 (bit 9) | Set to 0, reserved for future use |
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

| Mode ID | Hex | Description |
|---|---|---|
| 150 | 0x096 | AX.25 — Amateur packet radio |
| 151 | 0x097 | APRS — Automatic Packet Reporting System |
| 152 | 0x098 | VARA HF |
| 153 | 0x099 | VARA FM |
| 154 | 0x09A | Winlink |
| 155 | 0x09B | JS8Call |
| 156 | 0x09C | FT8 |
| 157 | 0x09D | FT4 |
| 158 | 0x09E | PSK31 |
| 159 | 0x09F | RTTY — Radioteletype |

#### Broadband / Multi-carrier

| Mode ID | Hex | Description |
|---|---|---|
| 180 | 0x0B4 | OFDM — Generic OFDM (parameters in metadata) |
| 181 | 0x0B5 | COFDM — Coded OFDM |

#### Legacy / Special

| Mode ID | Hex | Description |
|---|---|---|
| 200 | 0x0C8 | POCSAG — Paging |
| 201 | 0x0C9 | FLEX — Paging |
| 202 | 0x0CA | EAS — Emergency Alert System |
| 203 | 0x0CB | SAME — Specific Area Message Encoding |

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
| 234 | 0x0EA | WEFAX — Weather fax (satellite/HF) |

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

#### Satellite Telemetry and Beacon

| Mode ID | Hex | Description |
|---|---|---|
| 250 | 0x0FA | CW Beacon — Satellite Morse identifier |
| 251 | 0x0FB | FSK Telemetry — Generic satellite telemetry |
| 252 | 0x0FC | BPSK 1200 — CubeSat standard (AX.25) |
| 253 | 0x0FD | BPSK 9600 — Higher rate satellite downlink |
| 254 | 0x0FE | GMSK 9600 — GMSK satellite downlink |
| 255 | 0x0FF | GMSK 19200 — High rate GMSK downlink |

#### Satellite Voice and Data

| Mode ID | Hex | Description |
|---|---|---|
| 260 | 0x104 | Linear transponder — SSB/CW uplink/downlink |
| 261 | 0x105 | FM Satellite — Standard FM voice repeater |
| 262 | 0x106 | FM Satellite + CTCSS — FM with access tone |
| 263 | 0x107 | FUNcube — BPSK 1200 science telemetry |
| 264 | 0x108 | Es'hail-2 / QO-100 — NB transponder SSB |
| 265 | 0x109 | Es'hail-2 / QO-100 — WB transponder DATV |

#### Weather Satellite

| Mode ID | Hex | Description |
|---|---|---|
| 270 | 0x10E | NOAA APT — Automatic Picture Transmission |
| 271 | 0x10F | NOAA HRPT — High Resolution Picture Transmission |
| 272 | 0x110 | METEOR LRPT — Low Rate Picture Transmission |
| 273 | 0x111 | GOES LRIT — Low Rate Information Transmission |
| 274 | 0x112 | GOES HRIT — High Rate Information Transmission |
| 275 | 0x113 | Meteosat LRIT |
| 276 | 0x114 | DSB — Direct Sounder Broadcast |

#### Navigation Satellite

| Mode ID | Hex | Description |
|---|---|---|
| 280 | 0x118 | GPS L1 C/A — Coarse acquisition |
| 281 | 0x119 | GPS L2C |
| 282 | 0x11A | GLONASS L1 |
| 283 | 0x11B | Galileo E1 |
| 284 | 0x11C | ADS-B — Automatic Dependent Surveillance Broadcast |

---

### Experimental Range

Mode IDs 300–498 are reserved for experimental and user-defined modes. These are not
standardized and may be assigned freely for development and research purposes. An
implementer using this range should document their assignment locally to avoid conflicts
within their own project.

| Range | Hex Range | Description |
|---|---|---|
| 300–498 | 0x12C–0x1F2 | Experimental / user-defined |
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

## Future Work

- Definition of a standardized synchronization sequence for common modulations
- Per-mode metadata extensions (bandwidth, codec parameters, callsign) in an
  optional secondary field, also Golay-protected
- A public mode ID registry for experimental assignments
- GNU Radio 4.x reference block implementation
- Reference integration example combining preamble detection with gr-linux-crypto
  key retrieval and payload decryption in a single GNU Radio 4.x flowgraph
- Formal assignment of mode IDs for additional regional and emerging modes

---

## License

This specification is released into the public domain. No rights reserved.
Implementers are free to use, modify, and distribute this specification without
restriction. Attribution is appreciated but not required.
