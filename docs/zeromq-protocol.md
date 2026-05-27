# ZeroMQ Protocol Reference

This document describes the ZeroMQ message formats used by **gr-ident** and by the
**LinHT Handheld Transceiver** stack (M17 Project). It records where each convention was
observed in upstream source and which gr-ident functions implement or consume it.

For runnable examples see [`apps/flowgraphs/zmq-distributed-demo.md`](../apps/flowgraphs/zmq-distributed-demo.md)
and [`TESTING.md`](../TESTING.md).

---

## Summary

Two independent ZeroMQ conventions coexist in this repository:

| Family | Primary use | Socket pattern | Default transport |
|---|---|---|---|
| **LinHT** | LinHT GUI, baseband proxy, GNU Radio M17 flowgraphs | PUB/SUB | IPC under `/tmp/` |
| **gr-ident** | Standalone distributed flowgraphs, CI smoke tests | PUSH/PULL (IQ), PUB/SUB (control + results) | TCP localhost |

gr-ident **PTT control** is compatible with LinHT when `ZmqTxControlSub` uses `profile=linht`.
gr-ident **IQ streaming** (`ZmqPushSink` / `ZmqPullSource`) is **not** wire-compatible with
LinHT baseband sockets without a format adapter.

---

## External sources (LinHT / M17)

| Repository | Path | What it defines |
|---|---|---|
| [M17-Project/LinHT-utils](https://github.com/M17-Project/LinHT-utils) | [`tests/zmq_proxy/main.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/zmq_proxy/main.c) | Baseband PUB/SUB (`/tmp/bsb_rx`, `/tmp/bsb_tx`), PTT SUB on `ipc:///tmp/ptt_msg`, `string_to_pmt()`, SOT/EOT handling |
| [M17-Project/LinHT-utils](https://github.com/M17-Project/LinHT-utils) | [`tests/gui_test/test.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/gui_test/test.c) | GUI PUB bind on `ipc:///tmp/ptt_msg`, flowgraph aux PUB connect to `ipc:///tmp/fg_aux_data_in`, aux SUB on `ipc:///tmp/fg_aux_data_out`, PTT key SOT/EOT, SMS PMT pairs |
| [M17-Project/meta-linht-software](https://github.com/M17-Project/meta-linht-software) | Yocto layer / `linht-image.bb` | Ships LinHT system image with GNU Radio, M17 blocks, ZeroMQ runtime; does not define wire format (delegates to LinHT-utils / flowgraphs) |
| [M17-Project/meta-linht-sdr](https://github.com/M17-Project/meta-linht-sdr) | GNU Radio / SDR recipes | SDR stack dependency for LinHT; fork of meta-sdr |
| [gnuradio/gr4-incubator](https://github.com/gnuradio/gr4-incubator) | zeromq block templates | Origin of gr-ident `ZmqPushSink` / `ZmqPullSource` design |

---

## LinHT endpoints

All LinHT IPC paths use the `ipc://` scheme. Filesystem paths are under `/tmp/`.

| Endpoint | Socket (typical) | Bind / connect | Role |
|---|---|---|---|
| `ipc:///tmp/ptt_msg` | PUB (GUI) / SUB (proxy, subscribers) | GUI **binds** PUB; consumers **connect** SUB | PTT lifecycle: SOT / EOT PMT frames |
| `ipc:///tmp/fg_aux_data_in` | SUB (flowgraph) / PUB (GUI) | Flowgraph **binds** SUB; GUI **connects** PUB | Auxiliary messages to GNU Radio (SOT/EOT, SMS triggers) |
| `ipc:///tmp/fg_aux_data_out` | PUB (flowgraph) / SUB (GUI) | Flowgraph **binds** PUB; GUI **connects** SUB | Decoded M17 messages / stream metadata to GUI |
| `ipc:///tmp/bsb_rx` | PUB (proxy) / SUB (flowgraph) | Proxy **binds** PUB on `bsb_rx` | RX baseband from SX1255 toward flowgraph |
| `ipc:///tmp/bsb_tx` | SUB (proxy) / PUB (flowgraph) | Proxy **binds** SUB on `bsb_tx` | TX baseband from flowgraph toward SX1255 |

Observed in:

- `PTT_IPC`, `RX_IPC`, `TX_IPC` in [`zmq_proxy/main.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/zmq_proxy/main.c)
- `ptt_ipc`, `aux_fg_in_ipc`, `aux_fg_out_ipc` in [`gui_test/test.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/gui_test/test.c)

gr-ident constants (same strings):

- C++: `gr::grident::linht_ptt_endpoint`, `gr::grident::linht_fg_aux_endpoint` in
  [`blocklib/grident/include/gnuradio/grident/tx_control.h`](../blocklib/grident/include/gnuradio/grident/tx_control.h)
- Python: `LINHT_PTT_ENDPOINT`, `LINHT_FG_AUX_ENDPOINT` in
  [`python/grident/tx_control.py`](../python/grident/tx_control.py)

---

## LinHT PMT string wire format

LinHT encodes control symbols as a **single ZMQ message frame** (no topic prefix) using a
compact GNU Radio PMT string serialization.

### Layout

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 1 | PMT type | `0x02` (PMT string / ZMQ message type in LinHT code) |
| 1 | 2 | Length | Payload length, **big-endian** `uint16` |
| 3 | N | Payload | ASCII symbol bytes (not NUL-terminated on the wire) |

### PTT symbols

| Symbol | Meaning | Wire bytes (hex) | Length |
|---|---|---|---|
| `SOT` | Start of transmit (PTT pressed) | `02 00 03 53 4f 54` | 6 |
| `EOT` | End of transmit (PTT released) | `02 00 03 45 4f 54` | 6 |

### Reference implementation (LinHT)

```c
uint8_t string_to_pmt(uint8_t *pmt, const char *msg)
{
    pmt[0] = 2;
    uint16_t l = htons(strlen(msg));
    memcpy(&pmt[1], &l, sizeof(l));
    strcpy((char *)&pmt[3], msg);
    return 3 + strlen(msg);
}
```

Found identically in:

- [`zmq_proxy/main.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/zmq_proxy/main.c) (`string_to_pmt`)
- [`gui_test/test.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/gui_test/test.c) (`string_to_pmt`)

The proxy compares received PTT frames with `memcmp(pmt_buff, sot_pmt, 6)` and
`memcmp(pmt_buff, eot_pmt, 6)`.

### gr-ident implementation

| Language | Encode | Parse |
|---|---|---|
| C++ | (inline in smoke test) | `parse_linht_pmt_message()` then `parse_tx_control_message()` in [`blocklib/grident/lib/tx_control.cc`](../blocklib/grident/lib/tx_control.cc) |
| Python | `format_linht_pmt()` | `parse_linht_pmt()` / `parse_tx_control_message()` in [`python/grident/tx_control.py`](../python/grident/tx_control.py) |
| GR4 block | — | `gr::grident::zeromq::ZmqTxControlSub` calls `parse_tx_control_message()` in [`blocklib/grident/include/gnuradio-4.0/grident/zeromq/ZmqTxControlSub.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/zeromq/ZmqTxControlSub.hpp) |

Parser behaviour:

1. If byte 0 is `0x02`, decode BE length and map `SOT` -> TX on, `EOT` -> TX off.
2. Otherwise fall back to gr-ident plain text / JSON (see below).

### LinHT PTT message flow

```
LinHT GUI (gui_test)
  |  zmq_send(zmq_ptt_pub, sot_pmt, 6)     --> ipc:///tmp/ptt_msg
  |  zmq_send(zmq_fg_pub, sot_pmt, 6)      --> ipc:///tmp/fg_aux_data_in
  v
zmq_proxy SUB on ptt_msg          GNU Radio flowgraph SUB on fg_aux_data_in
  |  switch RF path to TX             |  start TX baseband chain
  v                                   v
zmq_proxy PUB bsb_rx (RX IQ)      flowgraph PUB bsb_tx (TX IQ)
```

On PTT release the GUI sends `EOT` to `fg_aux_data_in` first (with optional sustain delay),
then `EOT` to `ptt_msg`. Source: [`gui_test/test.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/gui_test/test.c)
lines handling `KEY_P` press/release.

**gr-ident wiring for preamble gating:** connect `ZmqTxControlSub` with
`profile=linht`, `endpoint=ipc:///tmp/ptt_msg`, `bind=false`, `topic=""` alongside the
existing zmq_proxy subscriber, or subscribe to `ipc:///tmp/fg_aux_data_in` if co-located
with the GNU Radio process that already binds that SUB socket.

---

## LinHT baseband IQ format

Defined in [`zmq_proxy/main.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/zmq_proxy/main.c).

| Parameter | Value |
|---|---|
| Sample rate | 500 kSa/s (`rate = 500000`) |
| Sample type | `int32_t`, interleaved I/Q (2 channels) |
| ZMQ message size | `ZMQ_LEN * sizeof(int32_t)` = **8192 bytes** (`ZMQ_LEN = 2048` int32 values = 1024 complex samples) |
| RX path | ALSA capture -> `zmq_send(zmq_pub, rx_buff, 8192)` on `ipc:///tmp/bsb_rx` |
| TX path | `zmq_recv(zmq_sub, tx_buff, ...)` on `ipc:///tmp/bsb_tx` -> ALSA playback |

Each ZMQ message is one ALSA period. The proxy treats `ZMQ_LEN * sizeof(int32_t)` as
`BYTES_PER_PERIOD`.

**Not implemented in gr-ident.** Use LinHT GNU Radio blocks or add a conversion block
(`int32` interleaved -> `complex<float>`) to connect gr-ident IQ detectors.

---

## LinHT auxiliary messages (SMS / M17 encoder)

Beyond bare SOT/EOT, the GUI sends **compound PMT messages** on `fg_aux_data_in` to trigger
M17 SMS transmission. Example from `m17_send_sms()` in
[`gui_test/test.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/gui_test/test.c):

```c
uint8_t pmt[1024] = {0x07, 0x02, 0x00, 0x03, 0x53, 0x4d, 0x53, 0x02};
memcpy(&pmt[10], msg, strlen(msg));
uint16_t l = htons(strlen(msg));
memcpy(&pmt[8], &l, sizeof(l));
zmq_send(zmq_fg_pub, pmt, 8 + 2 + l, 0);
```

This is a PMT pair (`"SMS"` key + string value). gr-ident **does not parse** these messages;
only `SOT` / `EOT` PMT strings are handled for TX gating today.

Flowgraph-to-GUI replies on `fg_aux_data_out` are parsed by `getMsgData()` in the GUI
(M17 decoded packets). gr-ident `PreambleResultZmqPub` uses a separate JSON schema (below).

---

## gr-ident native protocol

gr-ident defines its own ZeroMQ conventions for distributed development, testing, and
preamble-result publishing. These are **not** used by stock LinHT firmware unless you
deliberately bridge endpoints.

### TX / PTT control (`profile=grident`)

| Parameter | Default |
|---|---|
| Socket | SUB (receiver) / PUB (sender) |
| Endpoint | `tcp://127.0.0.1:5561` |
| Topic filter | `grident.tx` (multipart frame 0) |
| Body | UTF-8 JSON or plain text (multipart frame 1) |

**Accepted body payloads:**

| Body | TX state |
|---|---|
| `PTT_ON`, `TX`, `KEYDOWN`, `1`, `ON`, `SOT` | On |
| `PTT_OFF`, `RX`, `KEYUP`, `0`, `OFF`, `EOT` | Off |
| `{"ptt": true}`, `{"tx": 1}`, `{"key": true}` | On |
| `{"ptt": false}`, `{"tx": 0}`, `{"key": false}` | Off |

**Implementation:**

| Component | Location |
|---|---|
| Parser | `parse_tx_control_message()` — [`tx_control.cc`](../blocklib/grident/lib/tx_control.cc), [`tx_control.h`](../blocklib/grident/include/gnuradio/grident/tx_control.h) |
| GR4 subscriber block | `ZmqTxControlSub` — [`ZmqTxControlSub.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/zeromq/ZmqTxControlSub.hpp) |
| Python helpers | `format_tx_control_message()`, `send_tx_control(..., profile="grident")` — [`tx_control.py`](../python/grident/tx_control.py) |
| Tests | [`blocklib/grident/test/test_tx_control.cc`](../blocklib/grident/test/test_tx_control.cc), [`python/tests/test_tx_control.py`](../python/tests/test_tx_control.py), [`apps/gr4/grident_ptt_zmq_smoke.cpp`](../apps/gr4/grident_ptt_zmq_smoke.cpp) |

### IQ sample streaming (PUSH / PULL)

| Parameter | PUSH sink (sender) | PULL source (receiver) |
|---|---|---|
| Socket | PUSH | PULL |
| Default endpoint | `tcp://127.0.0.1:5555` | `tcp://127.0.0.1:5555` |
| Default bind | `true` | `false` |
| Payload | Raw binary: `sizeof(T) * N` bytes per message | Same |

Supported `T` types: `float`, `std::complex<float>`, `uint8_t`, `int32_t`, `std::string`,
and vectors thereof.

**Implementation:**

| Block | Header |
|---|---|
| `gr::grident::zeromq::ZmqPushSink<T>` | [`ZmqPushSink.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/zeromq/ZmqPushSink.hpp) |
| `gr::grident::zeromq::ZmqPullSource<T>` | [`ZmqPullSource.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/zeromq/ZmqPullSource.hpp) |
| Type traits | [`trait_helpers.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/zeromq/trait_helpers.hpp) |
| Umbrella include | [`GrIdentZmqBlocks.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/GrIdentZmqBlocks.hpp) |

Each input item (or bulk span element) becomes **one ZMQ message** with no framing header;
the receiver interprets byte length using the port item size.

### Preamble decode results (PUB / SUB)

Published after Golay preamble decode on the receive path.

| Parameter | Default |
|---|---|
| Socket | PUB |
| Endpoint | `tcp://127.0.0.1:5560` |
| Topic (optional frame 0) | `grident` |
| Body (frame 1) | UTF-8 JSON |

**JSON schema:**

```json
{
  "mode_id": 110,
  "digital": true,
  "encrypted": false,
  "metadata_present": false
}
```

**Implementation:** `gr::grident::zeromq::PreambleResultZmqPub` in
[`PreambleResultZmqPub.hpp`](../blocklib/grident/include/gnuradio-4.0/grident/zeromq/PreambleResultZmqPub.hpp).

The PUB block publishes **one JSON object per decoded preamble**. It does not include the
mode name string on the wire; subscribers map `mode_id` using
[`blocklib/grident/lib/mode_table.cc`](../blocklib/grident/lib/mode_table.cc) or
[`registry/experimental-modes.json`](../registry/experimental-modes.json).

---

## Worked examples: what happens when a mode is received

These examples trace the **gr-ident receive path** from IQ to ZeroMQ. They apply when
IQ reaches a gr-ident detect chain (file, `ZmqPullSource`, or a LinHT adapter on
`bsb_rx`). They do **not** describe LinHT `fg_aux_data_out` traffic, which carries M17
packet PMT pairs rather than gr-ident JSON.

### Receive pipeline (gr-ident)

```
IQ samples (48 kHz complex float, or adapted from LinHT int32 baseband)
    |
    v
Cpfsk4SyncCorrelator / detect_cpfsk4_preamble()     profile chosen by mode_id or search
    |
    v
Golay decode 24-bit codeword  -->  12-bit packed field (mode + flags)
    |
    v
PreambleDecode  -->  uint16 packed on block port
    |
    v
PreambleResultZmqPub  -->  tcp://127.0.0.1:5560  multipart [grident, JSON body]
    |
    v
Your subscriber  -->  mode router, gr-linux-crypto, external demod (Sleipnir, NFM, …)
```

Reference implementations:

| Step | C++ / GR4 | Python |
|---|---|---|
| IQ + detect | [`grident_receive_flowgraph.cpp`](../apps/gr4/grident_receive_flowgraph.cpp), `detect_cpfsk4_preamble()` | [`python/grident/iq_decode.py`](../python/grident/iq_decode.py) |
| Mode -> air profile | `cpfsk4_profile_for_mode_id()` in [`modulation_profile.cc`](../blocklib/grident/lib/modulation_profile.cc) | [`python/grident/modulation/registry.py`](../python/grident/modulation/registry.py) |
| Pack / unpack field | [`preamble_field.cc`](../blocklib/grident/lib/preamble_field.cc) | [`python/grident/preamble.py`](../python/grident/preamble.py) |
| ZMQ publish | `PreambleResultZmqPub::processOne()` | — |

### Preamble field bits (common to all modes)

The JSON body is derived from the 12-bit packed primary field (before Golay protection):

| Bits | Field | Meaning |
|---|---|---|
| 0–8 | `mode_id` | Mode number 0–511 (9 bits) |
| 9 | `metadata_present` | Secondary metadata Golay codeword follows |
| 10 | `encrypted` | Payload needs gr-linux-crypto key retrieval |
| 11 | `digital` | Digital payload (vs analog voice/data) |

---

### Example A — Mode 20 (0x014) NFM 12.5 kHz received

**Registry:** [`mode_table.cc`](../blocklib/grident/lib/mode_table.cc) — `"NFM 12.5 kHz"`, analog.

**Air interface:** CPFSK 4-FSK preamble on a 12.5 kHz NFM channel; profile `nfm_125_4800`,
sync sequence `sync_nfm`, 4800 sym/s, deviations 648 / 1944 Hz
([`modulation_profile.cc`](../blocklib/grident/lib/modulation_profile.cc) maps mode **20**
to this profile).

**Typical transmitted preamble flags:** `digital=false`, `encrypted=false`,
`metadata_present=false` (analog voice identification only).

**Packed field:** `0x0014` (decimal 20, no flag bits set).

**Golay codeword (primary):** `0xCB4014` (see fixture
[`python/tests/fixtures/common_modes/mode_020.json`](../python/tests/fixtures/common_modes/mode_020.json)).

#### Step 1 — Detect from IQ (no ZeroMQ yet)

```bash
./build-gr4/grident_receive_flowgraph \
  python/tests/fixtures/common_modes/mode_020.cf32 20
```

Expected stdout:

```
OK mode_id=20 packed=0x0014 sync_start=47998
```

#### Step 2 — ZeroMQ message on successful decode

When the same detect result passes through `PreambleResultZmqPub` (default
`endpoint=tcp://127.0.0.1:5560`, `topic=grident`), subscribers receive **two frames**:

| Frame | Content (example) |
|---|---|
| 0 (topic) | `grident` (7 bytes ASCII) |
| 1 (body) | `{"mode_id":20,"digital":false,"encrypted":false,"metadata_present":false}` |

Wire body (UTF-8, 67 bytes):

```json
{"mode_id":20,"digital":false,"encrypted":false,"metadata_present":false}
```

#### Step 3 — Subscriber behaviour

A process subscribed to port **5560** should:

1. Parse JSON and read `mode_id == 20`.
2. Look up **NFM 12.5 kHz** in the mode table (analog, not encrypted).
3. **Skip** gr-linux-crypto (bit 10 is false).
4. Route the **payload after the preamble burst** to an NFM discriminator / audio sink
   (standard 12.5 kHz channel FM demod), not to a digital codec chain.

Example subscriber with simple routing:

```python
import json
import zmq

MODES = {
    20: {"name": "NFM 12.5 kHz", "demod": "nfm_analog"},
    300: {"name": "Sleipnir", "demod": "sleipnir_qpsk"},
}

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB)
sub.connect("tcp://127.0.0.1:5560")
sub.setsockopt_string(zmq.SUBSCRIBE, "grident")

topic, payload = sub.recv_multipart()
result = json.loads(payload.decode())

mode_id = result["mode_id"]
info = MODES.get(mode_id, {"name": "unknown", "demod": "generic"})

if result["encrypted"]:
    raise RuntimeError("encrypted payload — call gr-linux-crypto first")

if mode_id == 20 and not result["digital"]:
    print(f"Route to NFM analog demod: {info['name']}")
elif mode_id == 300 and result["digital"]:
    print(f"Route to Sleipnir multi-carrier demod: {info['name']}")
```

For mode **20**, gr-ident has **finished its job** at this point: it identified the mode
on the air. Voice recovery uses ordinary NFM demodulation of the IQ stream continuing
after the ~200-sample preamble burst (`nfm_125_4800` at 48 kHz).

#### LinHT note

Stock LinHT GUI listens on `ipc:///tmp/fg_aux_data_out` for **M17** decoded messages
(`getMsgData()` in [`gui_test/test.c`](https://github.com/M17-Project/LinHT-utils/blob/main/tests/gui_test/test.c)).
It does **not** consume gr-ident JSON on TCP 5560. To display mode 20 gr-ident results on
LinHT you need a bridge process or a custom subscriber.

---

### Example B — Mode 300 (0x12C) Sleipnir received

**Registry:** experimental assignment in
[`registry/experimental-modes.json`](../registry/experimental-modes.json) and
[`docs/experimental-mode-registry.md`](experimental-mode-registry.md) — **Sleipnir**
([gr-sleipnir](https://github.com/Supermagnum/gr-sleipnir)), 8-carrier QPSK digital voice.

**Typical transmitted preamble flags:** `digital=true`, `encrypted=false` (open payload),
`metadata_present=false`.

**Packed field:** `0x092C` (mode 300 + bit 11 set: 300 + 2048 = 2348).

**Golay codeword (primary, open):** `0x3E592C`.

If the operator enables encryption (bit 10):

| Flags | Packed | Codeword |
|---|---|---|
| digital, encrypted | `0x0D2C` | `0x23ED2C` |

#### Step 1 — Detect from IQ (current gr-ident limitation)

Mode **300** is **not** mapped in `cpfsk4_profile_for_mode_id()` today
([`modulation_profile.cc`](../blocklib/grident/lib/modulation_profile.cc) lists modes
20, 21, 22, 30, 40, 100, 103, 104, 107, 108, 110, 120 — not 300). Running:

```bash
./build-gr4/grident_receive_flowgraph capture.cf32 300
```

prints `No CPFSK profile for mode_id 300` and exits with failure until a Sleipnir
CPFSK/QPSK profile and sync sequence are added.

Sleipnir uses a **different payload air interface** (multi-carrier QPSK) than the NFM
CPFSK preamble burst; only the **12-bit gr-ident preamble field** is mode 300 — the
post-preamble demod is external (gr-sleipnir).

#### Step 2 — ZeroMQ message (once preamble is decoded)

After a successful Golay decode (from IQ with a future profile, or from
`PreambleDecode` in a flowgraph fed a known codeword), `PreambleResultZmqPub` emits:

| Frame | Content |
|---|---|
| 0 | `grident` |
| 1 | `{"mode_id":300,"digital":true,"encrypted":false,"metadata_present":false}` |

Encrypted variant body:

```json
{"mode_id":300,"digital":true,"encrypted":true,"metadata_present":false}
```

#### Step 3 — Subscriber behaviour

On `mode_id == 300` and `digital == true`:

1. Confirm assignment in [`registry/experimental-modes.json`](../registry/experimental-modes.json).
2. If `encrypted == true`, invoke **gr-linux-crypto** before payload FEC
   ([`gr-linux-crypto-demo.md`](../apps/flowgraphs/gr-linux-crypto-demo.md)).
3. Hand IQ **after the preamble** to **gr-sleipnir** (or your Sleipnir demod), not to
   NFM or M17 blocks.
4. Do **not** expect LinHT M17 flowgraphs to demod Sleipnir; M17 and Sleipnir are
   separate digital voice systems sharing only the gr-ident mode ID space.

---

### Example C — Distributed receive (IQ over ZeroMQ, any mode)

**Process A** pushes IQ from a file or SDR:

```
[IQ source] -> ZmqPushSink<std::complex<float>>  endpoint=tcp://*:5555  bind=true
```

**Process B** pulls, detects, publishes (mode 20 shown):

```
ZmqPullSource<std::complex<float>>  endpoint=tcp://localhost:5555  bind=false
    -> Cpfsk4PreambleDetect  (or library detect_cpfsk4_preamble)
    -> PreambleDecode
    -> PreambleResultZmqPub  endpoint=tcp://*:5560  bind=true
```

When mode **20** preambles appear in the IQ stream, Process B publishes the JSON from
Example A on **5560**. When mode **300** preambles appear (once detection is implemented),
Process B publishes the JSON from Example B.

---

### Example D — Transmit side (PTT + preamble mode selection)

Preamble **insertion** uses `PreambleOnPtt`, not the preamble JSON PUB. The operator
selects `mode_id` on the block; the Golay burst on key-down encodes that ID.

**LinHT PTT + mode 20 preamble (receive-compatible analog ID):**

```
ZmqTxControlSub  profile=linht  endpoint=ipc:///tmp/ptt_msg  bind=false
    -> PreambleOnPtt  mode_id=20  digital=false  encrypted=false
        preamble_out -> CPFSK modulator -> ZmqPushSink / RF
        tx_out       -> voice gate
```

On LinHT GUI key-down (`SOT`), `PreambleOnPtt` emits codeword `0xCB4014` once; receivers
decode mode **20** as in Example A.

**Mode 300 Sleipnir transmit (digital ID):**

```
PreambleOnPtt  mode_id=300  digital=true  encrypted=false
```

Emits Golay codeword `0x3E592C` on key-down. Payload bits after the burst must be
generated by a Sleipnir modulator, not by gr-ident alone.

**gr-ident profile PTT (lab / TCP):**

```python
from grident.tx_control import TxControlState, send_tx_control

send_tx_control("tcp://127.0.0.1:5561", TxControlState.ON, profile="grident")
# flowgraph emits preamble for configured mode_id, then gates voice
send_tx_control("tcp://127.0.0.1:5561", TxControlState.OFF, profile="grident")
```

---

### Mode receive summary

| Mode | Hex | Name | Detect today | ZMQ JSON (typical) | Subscriber action |
|---:|---|---|---|---|---|
| 20 | 0x014 | NFM 12.5 kHz | Yes (`nfm_125_4800`) | `"mode_id":20,"digital":false,...` | NFM analog demod; no crypto |
| 300 | 0x12C | Sleipnir | No CPFSK profile yet | `"mode_id":300,"digital":true,...` | gr-sleipnir demod; crypto if bit 10 set |

---

## Compatibility matrix

| Channel | LinHT format | gr-ident format | Compatible today |
|---|---|---|---|
| PTT / TX control | Single-part PMT `SOT`/`EOT`, no topic | Multipart `[grident.tx, body]` or LinHT PMT via auto-parser | **Yes** (`profile=linht`) |
| RX / TX baseband IQ | PUB/SUB, `int32` interleaved, 8192 B/msg | PUSH/PULL, `complex<float>` binary | **No** (adapter required) |
| Decoded metadata to GUI | PMT pairs on `fg_aux_data_out` | JSON PUB on TCP 5560 | **No** (different schema and transport); use [gateway adapter](gateway-integration.md) |
| SMS / encoder triggers | Compound PMT on `fg_aux_data_in` | Not implemented | **No** |

---

## Quick reference: default endpoints

| Purpose | LinHT | gr-ident |
|---|---|---|
| PTT | `ipc:///tmp/ptt_msg` | `tcp://127.0.0.1:5561` |
| Flowgraph aux in | `ipc:///tmp/fg_aux_data_in` | — |
| Flowgraph aux out | `ipc:///tmp/fg_aux_data_out` | — |
| Baseband RX | `ipc:///tmp/bsb_rx` | — |
| Baseband TX | `ipc:///tmp/bsb_tx` | — |
| Distributed IQ | — | `tcp://127.0.0.1:5555` (PUSH/PULL) |
| Preamble JSON | — | `tcp://127.0.0.1:5560` (PUB, topic `grident`) |

---

## Related gr-ident files

| File | Role |
|---|---|
| [`apps/flowgraphs/ptt_preamble.gr.yaml`](../apps/flowgraphs/ptt_preamble.gr.yaml) | Reference flowgraph: LinHT profile PTT -> `PreambleOnPtt` |
| [`apps/flowgraphs/zmq-distributed-demo.md`](../apps/flowgraphs/zmq-distributed-demo.md) | Operational wiring guide |
| [`docs/gateway-integration.md`](gateway-integration.md) | VoIP gateway adapters, ZMQ, gr-linux-crypto |
| [`TESTING.md`](../TESTING.md) | PTT/ZMQ smoke test prerequisites |
| [`blocklib/grident/blocks/README.md`](../blocklib/grident/blocks/README.md) | Block inventory |
