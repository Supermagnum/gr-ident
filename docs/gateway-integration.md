# Gateway Integration Reference

This document describes how **voice-linking and VoIP gateway software** (EchoLink,
IRLP, AllStar Link, Mumble, Wires-X, D-STAR reflectors) can integrate with gr-ident
**ZeroMQ messaging** and **[gr-linux-crypto](https://github.com/Supermagnum/gr-linux-crypto)**
payload protection.

It is a design reference for gateway maintainers. gr-ident does not ship gateway
protocol stacks; it provides RF-side preamble detection, mode identification, and
ZMQ control/result buses that a gateway adapter connects to.

Related:

- [ZeroMQ protocol](zeromq-protocol.md) — wire formats, LinHT compatibility, mode examples
- [gr-linux-crypto demo flowgraph](../apps/flowgraphs/gr-linux-crypto-demo.md) — in-process GR4 path
- [Security integration](../README.md#security-integration--gr-linux-crypto) — preamble bit 10

---

## Roles

| Component | Responsibility |
|---|---|
| **GNU Radio + gr-ident** | RF demod/mod, Golay preamble detect/insert, optional IQ streaming over ZMQ |
| **Gateway software** | VoIP/linking protocol (EchoLink, IRLP, Asterisk/app_rpt, Mumble, Wires-X, xlxd/urfd, …) |
| **Gateway adapter** | Process or module that subscribes to gr-ident ZMQ, routes by `mode_id`, invokes gr-linux-crypto when needed, and bridges audio/PTT to the gateway |

Typical stack:

```
[RF] <--> [GNU Radio flowgraph + gr-ident blocks]
              |                    ^
              | IQ (optional)      | PTT (ZMQ)
              v                    |
         [Gateway adapter] -------+  (audio UDP/ALSA/USRP, PTT GPIO/PTY)
              |
              v
         [EchoLink / IRLP / AllStar / Mumble / …]
```

---

## ZeroMQ interfaces to implement

See [zeromq-protocol.md](zeromq-protocol.md) for full byte-level detail.

### Receive path — preamble results (subscribe)

| Parameter | Default (gr-ident profile) |
|---|---|
| Socket | SUB |
| Endpoint | `tcp://127.0.0.1:5560` |
| Topic | `grident` (multipart frame 0) |
| Body | UTF-8 JSON (frame 1) |

**JSON schema** (published by `PreambleResultZmqPub` after each successful decode):

```json
{
  "mode_id": 110,
  "digital": true,
  "encrypted": false,
  "metadata_present": false
}
```

The adapter should:

1. Parse JSON on every message.
2. Map `mode_id` to a gateway route (see [linking mode table](#linking-mode-ids-110115) below).
3. If `encrypted == true`, call gr-linux-crypto **before** passing payload audio to the gateway or demodulator.
4. If `metadata_present == true`, expect a secondary metadata decode on the GR side (bandwidth, codec); extend JSON handling when that field is added to the PUB block.

**Example subscriber (Python):**

```python
import json
import zmq

def subscribe_preamble(endpoint: str = "tcp://127.0.0.1:5560", topic: b = b"grident"):
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.connect(endpoint)
    sub.setsockopt(zmq.SUBSCRIBE, topic)
    while True:
        _topic, payload = sub.recv_multipart()
        yield json.loads(payload.decode())
```

Use `python/grident/tx_control.py` patterns for consistent parsing on the TX side.

### Transmit path — PTT / keying (publish or subscribe)

| Profile | Endpoint | Format |
|---|---|---|
| LinHT (default) | `ipc:///tmp/ptt_msg` | Single-part PMT `SOT` / `EOT` |
| gr-ident (lab) | `tcp://127.0.0.1:5561` | Multipart `[grident.tx, body]` JSON or plain text |

Wire `ZmqTxControlSub` in the GR4 flowgraph to `PreambleOnPtt` so the Golay burst is emitted on key-down. The gateway adapter either **publishes** PTT (when the gateway keys the radio) or **forwards** gateway COS/PTT to this socket.

Helpers: `send_tx_control()` in [`python/grident/tx_control.py`](../python/grident/tx_control.py).

### Optional — distributed IQ (PUSH/PULL)

When the SDR process and gateway adapter run on different hosts:

| Direction | Socket | Default endpoint |
|---|---|---|
| IQ to GR detect chain | PUSH → PULL | `tcp://host:5555` |
| Float complex samples | Raw binary, no header | `sizeof(complex<float>) * N` per message |

LinHT baseband (`ipc:///tmp/bsb_rx`, int32 interleaved) requires a format adapter before gr-ident `ZmqPullSource`.

---

## Linking mode IDs (110–115)

These mode IDs label **linked voice** on the RF side. They do not embed the VoIP protocol;
the gateway adapter selects the IP service after preamble decode.

| Mode ID | Hex | Name | gr-ident RF profile | Typical gateway software | GNU Radio bridge today |
|---:|---|---|---|---|---|
| 110 | 0x06E | EchoLink | `nfm_125_4800` (FM gateway) | [SvxLink](https://github.com/sm0svx/svxlink) EchoLink module | SvxLink `AUDIO_DEV=udp:…` ↔ GR (documented) |
| 111 | 0x06F | IRLP | (operator-defined; often NFM) | IRLP node + board | Audio/PTT to node; no open GR IRLP block |
| 112 | 0x070 | AllStar Link | (operator-defined; often NFM) | [ASL3](https://github.com/allstarlink/asl3) / `app_rpt` | USRP channel driver ↔ UDP/audio |
| 113 | 0x071 | Mumble | (operator-defined) | Mumble server + client | [QRadioLink](https://qradiolink.org/docs/features/voip.html), [radio-gateway](https://github.com/ukbodypilot/radio-gateway) |
| 114 | 0x072 | Wires-X | `c4fm_4800` if digital RF | Yaesu Wires-X node (proprietary) | C4FM air only; room link via MMDVM/BrandMeister, not GR |
| 115 | 0x073 | D-STAR Reflector | D-STAR sync (`sync_dstar`) | [xlxd](https://github.com/n7tae/new-xlxd) / [urfd](https://github.com/n7tae/urfd) / gateway | Reflector is IP daemon; GR on RF leg |

**Mode 110 (EchoLink)** is the only linking ID with a gr-ident test vector today (`mode_110.cf32`, profile `nfm_125_4800`). Modes 111–115 are registered in [`mode_table.cc`](../blocklib/grident/lib/mode_table.cc) for identification; operators assign the RF profile to match their gateway's analog or digital link radio.

---

## Gateway adapter design

### Recommended module boundaries

1. **ZMQ I/O** — SUB on 5560, optional PUB/SUB on PTT endpoint, optional PUSH/PULL IQ.
2. **Mode router** — Table from `mode_id` → `{gateway, demod, profile}`.
3. **Crypto gate** — If `encrypted`, call gr-linux-crypto; else pass through.
4. **Audio bridge** — Sample-rate conversion between GR (often 48 kHz float) and gateway (often 8 kHz mono PCM for VoIP).
5. **PTT bridge** — Map gateway PTT/COS to LinHT SOT/EOT or gr-ident PTT messages.

### Mode router example

```python
LINKING_ROUTES = {
    110: {"gateway": "svxlink", "service": "echolink", "demod": "nfm"},
    111: {"gateway": "irlp", "demod": "nfm"},
    112: {"gateway": "allstar", "demod": "nfm"},
    113: {"gateway": "mumble", "demod": "nfm"},
    114: {"gateway": "wiresx", "demod": "c4fm"},
    115: {"gateway": "dstar_reflector", "demod": "dstar"},
}

def route(result: dict) -> dict | None:
    return LINKING_ROUTES.get(result["mode_id"])
```

### Receive sequence (adapter pseudocode)

```python
def on_preamble(result: dict, iq_stream, gateway_audio_sink):
    route = route_mode(result)
    if route is None:
        log_unknown_mode(result["mode_id"])
        return

    if result["encrypted"]:
        key = retrieve_key_gr_linux_crypto(policy="gnupg-agent")  # see below
        payload = decrypt_payload(key, iq_stream, after_preamble=True)
    else:
        payload = demod_payload(iq_stream, profile=route["demod"], after_preamble=True)

    gateway_audio_sink.send(payload, service=route["gateway"])
```

### Transmit sequence (gateway keys RF)

```python
def on_gateway_ptt_down(mode_id: int, gateway_name: str):
    send_tx_control(LINHT_PTT_ENDPOINT, TxControlState.ON)   # or profile="grident"
    # GR flowgraph PreambleOnPtt emits Golay burst for mode_id
    gateway.forward_tx_audio_to_gr()

def on_gateway_ptt_up():
    gateway.stop_tx_audio()
    send_tx_control(LINHT_PTT_ENDPOINT, TxControlState.OFF)
```

---

## Modifying gateway software

Gateways are not modified to speak gr-ident on the air. Modifications add a **sidecar adapter**
or patch **audio/PTT hooks** so the existing gateway sees the same PCM and keying it already expects.

### EchoLink via SvxLink (mode 110)

**Gateway:** [SvxLink](https://github.com/sm0svx/svxlink) with EchoLink module.

**Integration approach:**

1. Configure SvxLink TX/RX with UDP audio (documented for GNU Radio):

   ```ini
   [TX1]
   TYPE=LOCAL
   AUDIO_DEV=udp:127.0.0.1:1235
   PTT_TYPE=PTY
   PTT_PTY=/tmp/grident_ptt
   ```

2. Run GNU Radio between UDP port 1235 and the RF chain (NBFM + gr-ident preamble detect on RX; `PreambleOnPtt` on TX).

3. Add a small process that:
   - SUBscribes to `tcp://127.0.0.1:5560` and logs or displays `mode_id == 110`.
   - Monitors `/tmp/grident_ptt` (or forwards LinHT SOT/EOT) for PTT from SvxLink.

**Reference community wiring:** [svxlink_to_rpitx](https://github.com/antonjan/svxlink_to_rpitx), [SvxLink UDP manual note](https://github.com/sm0svx/svxlink/issues/454).

### IRLP (mode 111)

**Gateway:** IRLP node software + IRLP interface board.

**Integration approach:**

1. Do not implement IRLP inside GNU Radio; wire **discriminator audio** and **PTT/COS** from the GR modem to the IRLP DB-9 interface (same as a conventional repeater controller).

2. Optional adapter: on preamble JSON with `mode_id == 111`, set an internal "link mode" flag so the node scripts know the transmission was tagged as IRLP-linked voice.

3. [EchoIRLP](https://www.irlp.net/) combines EchoLink + IRLP on one node; use SvxLink UDP path for the EchoLink leg and standard IRLP hardware for IRLP.

### AllStar Link (mode 112)

**Gateway:** Asterisk + `app_rpt` ([ASL3](https://github.com/allstarlink/asl3)).

**Integration approach:**

1. Use the **USRP channel driver** (AllStar's audio-over-UDP protocol, not Ettus hardware) between Asterisk and your adapter:

   ```ini
   ; rpt.conf (conceptual)
   [node_12345]
   rxchannel=Radio/your_radio_channel
   txchannel=Radio/your_radio_channel
   ```

2. Bridge USRP packets to GNU Radio float audio (see [usrp-go](https://github.com/dbehnke/usrp-go) for protocol reference).

3. Adapter SUB on 5560: when `mode_id == 112`, ensure rpt logic connects to the intended AllStar hub or stays in local RF mode.

4. ASL3 includes EchoLink bridging natively; gr-ident mode 110 vs 112 distinguishes RF identification of EchoLink vs native AllStar traffic.

### Mumble (mode 113)

**Gateway:** Mumble server + client, or embedded server in [radio-gateway](https://github.com/ukbodypilot/radio-gateway).

**Integration approach:**

1. Treat Mumble as **audio sink/source** in the adapter ([pymumble](https://github.com/oopsbagel/pymumble) or QRadioLink Mumble linking).

2. On `mode_id == 113`, route demodulated voice to the configured Mumble channel; on PTT from Mumble, key GR TX with `mode_id` 113 in `PreambleOnPtt`.

3. [QRadioLink](https://qradiolink.org/docs/features/voip.html) documents star-topology Mumble linking for SDR nodes.

### Wires-X (mode 114)

**Gateway:** Yaesu Wires-X node (HRI-200 + Windows software) or server-side bridges (BrandMeister WiresXLink).

**Integration approach:**

1. GNU Radio handles **C4FM air** (`c4fm_4800` profile); Wires-X **room protocol** stays in Yaesu or MMDVM bridge software.

2. Adapter uses preamble JSON only to label traffic as mode 114; room selection remains in Wires-X or DMR bridge config.

3. Do not expect `PreambleResultZmqPub` on LinHT `fg_aux_data_out`; that path carries M17 PMT messages, not gr-ident JSON.

### D-STAR Reflector (mode 115)

**Gateway:** Reflector daemon ([xlxd](https://github.com/n7tae/new-xlxd), [urfd](https://github.com/n7tae/urfd)) or D-STAR repeater gateway client.

**Integration approach:**

1. gr-ident detects D-STAR-style preamble (`sync_dstar`); reflector **DCS/REF/XRF** connectivity remains in xlxd/urfd.

2. Adapter on `mode_id == 115`: trigger reflector module selection or notify the gateway to link the RF leg to the configured reflector.

3. Digital voice codec (AMBE) transcoding stays in the D-STAR gateway or urfd/tcd, not in gr-ident.

---

## gr-linux-crypto integration

Preamble **bit 10** (`encrypted` in JSON) means the payload after the Golay burst requires
key material before demodulation or before forwarding decoded audio to an open VoIP link.

### When to invoke crypto

| `encrypted` | Adapter action |
|---|---|
| `false` | Demod payload, send clear audio to gateway (optional Ed25519 verify per gr-linux-crypto signing docs) |
| `true` | Retrieve key via gr-linux-crypto, decrypt stream, then demod or forward |

### Key retrieval (conceptual)

Integrate with gr-linux-crypto in the adapter process or in a GR block after `PreambleDecode`:

```python
# Pseudocode — align with gr-linux-crypto API in your installed version
def retrieve_key_gr_linux_crypto(policy: str = "gnupg-agent"):
    import gr_linux_crypto  # OOT module / Python bindings
    return gr_linux_crypto.retrieve_key(source=policy)
```

Supported key sources (see [README](../README.md#supported-key-sources-via-gr-linux-crypto)):

- Linux kernel keyring (`keyctl`)
- Nitrokey / OpenPGP card
- GnuPG agent

### Encrypted linking modes

Linking modes 110–115 may carry **encrypted** linked voice (bit 10 set) when the IP bridge
or RF leg uses gr-linux-crypto. The adapter must:

1. Refuse to push audio to EchoLink/Mumble/AllStar public reflectors until decrypted (policy-dependent).
2. Pass ciphertext only to demod paths that understand gr-linux-crypto framing.
3. Set `encrypted=true` in `PreambleOnPtt` / `PreambleSource` on TX when the gateway sources encrypted content.

### Metadata field (bit 9)

When `metadata_present == true`, decode the secondary Golay codeword (GR4 `MetadataDecode` or Python `metadata_field.py`) for bandwidth and codec hints before selecting gr-linux-crypto decryption profile.

Full in-graph reference: [gr-linux-crypto-demo.md](../apps/flowgraphs/gr-linux-crypto-demo.md).

---

## Deployment patterns

### A — Single host (repeater)

```
SvxLink/ASL  <--UDP/ALSA-->  GNU Radio + gr-ident  <--->  Radio
                                |
                                +-- PUB preamble JSON :5560 (optional local dashboard)
```

### B — Split SDR and gateway

```
[SDR host]  ZmqPushSink IQ :5555  --->  [Gateway host]  ZmqPullSource
                                              |
                                              +-- detect + PreambleResultZmqPub :5560
                                              +-- SvxLink / ASL / Mumble
```

### C — LinHT handheld + gr-ident preamble

```
LinHT GUI  -- SOT/EOT -->  ipc:///tmp/ptt_msg  -->  ZmqTxControlSub  -->  PreambleOnPtt
GR detect  -- JSON ----->  adapter subscribes (bridge to desktop gateway if needed)
```

---

## Testing

1. Verify preamble JSON with fixture IQ:

   ```bash
   ./build-gr4/grident_receive_flowgraph python/tests/fixtures/common_modes/mode_110.cf32 110
   ```

2. Run adapter SUB against a flowgraph publishing on `:5560`.

3. PTT loopback: `send_tx_control(..., profile="linht")` and confirm `grident_ptt_zmq_smoke` behaviour (see [TESTING.md](../TESTING.md)).

4. Regenerate test report:

   ```bash
   PYTHONPATH=python python3 python/grident/generate_docs.py --test-results-only
   ```

---

## Summary

| Layer | Technology |
|---|---|
| RF identification | gr-ident Golay preamble + mode ID 110–115 |
| Control bus | ZeroMQ PTT (LinHT PMT or gr-ident multipart) |
| Result bus | ZeroMQ PUB JSON on port 5560 |
| Payload protection | gr-linux-crypto when `encrypted: true` |
| VoIP protocols | Existing gateway software (SvxLink, ASL, IRLP, Mumble, …) via audio/PTT bridge |

Implementers add a **gateway adapter** rather than forking gr-ident or the VoIP stack to
parse RF preambles. See [zeromq-protocol.md](zeromq-protocol.md) for wire formats and
mode 20 / 300 worked examples.
