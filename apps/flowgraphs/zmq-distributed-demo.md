# ZeroMQ Distributed Flowgraphs

The gr-ident GNU Radio 4.x plugin includes ZeroMQ blocks for distributed edges and
preamble-result publishing. Build with libzmq installed (`libzmq3-dev` on Debian/Ubuntu).

Normative wire-format reference (LinHT vs gr-ident, upstream source paths):
[`docs/zeromq-protocol.md`](../../docs/zeromq-protocol.md).

## Build

```bash
cmake -B build-gr4 -DCMAKE_PREFIX_PATH=/opt/gnuradio4-gcc
cmake --build build-gr4
```

When `pkg-config` finds `libzmq`, CMake builds an additional shared plugin
`GrIdentZmqBlocks` alongside `GrIdentBlocks`.

## Registered blocks

| Block | Socket | Purpose |
|---|---|---|
| `gr::grident::zeromq::ZmqPushSink<T>` | PUSH | Send sample streams (IQ, scalars, strings) |
| `gr::grident::zeromq::ZmqPullSource<T>` | PULL | Receive sample streams from a remote PUSH |
| `gr::grident::zeromq::PreambleResultZmqPub` | PUB | Broadcast decoded preamble JSON |
| `gr::grident::zeromq::ZmqTxControlSub` | SUB | Receive TX/PTT key commands |

Supported `T` types: `float`, `std::complex<float>`, vectors thereof, `std::string`.

## TX / PTT preamble gating (transmit path)

Preamble insertion is **not** automatic on every transmission. Wire a TX control stream into
`gr::grident::PreambleOnPtt` so the Golay preamble burst is emitted only on key-down.

### LinHT Handheld Transceiver (default profile)

LinHT publishes PTT as **single-part** GNU Radio PMT strings on IPC (see
[M17-Project/LinHT-utils](https://github.com/M17-Project/LinHT-utils) `tests/zmq_proxy`):

| Endpoint | Role |
|---|---|
| `ipc:///tmp/ptt_msg` | GUI PUB; flowgraph SUB connects (via zmq_proxy) |
| `ipc:///tmp/fg_aux_data_in` | Alternate GUI-to-flowgraph aux path |

Wire `ZmqTxControlSub` with `profile=linht`, `endpoint=ipc:///tmp/ptt_msg`, `bind=false`,
`topic=""` (empty). Payloads:

- **SOT** (start of transmit): bytes `02 00 03 53 4f 54` (PMT string `"SOT"`)
- **EOT** (end of transmit): bytes `02 00 03 45 4f 54` (PMT string `"EOT"`)

Python helper:

```python
from grident.tx_control import TxControlState, send_tx_control

send_tx_control("ipc:///tmp/ptt_msg", TxControlState.ON)   # LinHT SOT
send_tx_control("ipc:///tmp/ptt_msg", TxControlState.OFF)  # LinHT EOT
```

**Process B — GNU Radio 4 transmit flowgraph (LinHT):**

```
ZmqTxControlSub  profile=linht  endpoint=ipc:///tmp/ptt_msg  bind=false  topic=""
    -> PreambleOnPtt  mode_id=110
        preamble_out -> [sync + modulator]
        tx_out       -> [payload gate / voice mux]
```

LinHT baseband IQ uses separate PUB/SUB sockets (`ipc:///tmp/bsb_rx`, `ipc:///tmp/bsb_tx`)
with int32 interleaved I/Q (2048 complexes per message). gr-ident `ZmqPushSink` /
`ZmqPullSource` use float complex PUSH/PULL and are not wire-compatible with LinHT baseband
without a format adapter.

### gr-ident profile (standalone / distributed testing)

**Process A — external PTT (Python, GPIO daemon, or another host):**

```python
import zmq
import json

ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.connect("tcp://127.0.0.1:5561")

def ptt(on: bool):
    pub.send_multipart([b"grident.tx", json.dumps({"ptt": on}).encode()])

ptt(True)   # key down: preamble burst starts in flowgraph B
# ... voice payload ...
ptt(False)  # key up
```

Or use `python/grident/tx_control.py`:

```python
from grident.tx_control import TxControlState, send_tx_control

send_tx_control("tcp://127.0.0.1:5561", TxControlState.ON, profile="grident")
send_tx_control("tcp://127.0.0.1:5561", TxControlState.OFF, profile="grident")
```

**Process B — GNU Radio 4 transmit flowgraph:**

```
ZmqTxControlSub  profile=grident  endpoint=tcp://127.0.0.1:5561  bind=true  topic=grident.tx
    -> PreambleOnPtt  mode_id=110
        preamble_out -> [sync + modulator]
        tx_out       -> [payload gate / voice mux]
```

Accepted grident control payloads (plain text or JSON):

- `PTT_ON`, `PTT_OFF`, `TX`, `RX`, `KEYDOWN`, `KEYUP`, `1`, `0`
- `{"ptt": true}`, `{"ptt": false}`, `{"tx": 1}`, `{"tx": 0}`

`PreambleOnPtt` emits one primary Golay codeword on each 0-to-1 transition on `tx_in`, plus
an optional metadata codeword when `metadata_present` is set. Gate voice samples with `tx_out`.

## Runnable flowgraph tools

After building, run automated smoke tests:

```bash
ctest --test-dir build-gr4 --output-on-failure -R 'grident_(receive|ptt|run)'
```

Or manually:

```bash
./build-gr4/grident_receive_flowgraph capture.cf32 110
./build-gr4/grident_ptt_zmq_smoke
./build-gr4/grident_run_flowgraph apps/flowgraphs/receive_iq_detect.gr.yaml \
  REPLACE_ME.cf32=capture.cf32
```

See [`TESTING.md`](../../TESTING.md) for prerequisites (including `libzmq3-dev` for PTT tests).

## IQ loopback (two processes)

**Process A — RF / file source pushing IQ:**

```
[IQ source] -> ZmqPushSink<std::complex<float>>  endpoint=tcp://*:5555  bind=true
```

**Process B — gr-ident detect chain pulling IQ:**

```
ZmqPullSource<std::complex<float>>  endpoint=tcp://localhost:5555  bind=false
    -> [channel filter / preamble detect / Golay decode]
    -> PreambleResultZmqPub  endpoint=tcp://*:5560  bind=true
```

## Preamble JSON subscriber (Python)

```python
import json
import zmq

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB)
sub.connect("tcp://127.0.0.1:5560")
sub.setsockopt_string(zmq.SUBSCRIBE, "grident")

while True:
    topic, payload = sub.recv_multipart()
    print(json.loads(payload.decode()))
```

Example output:

```json
{"mode_id": 110, "digital": true, "encrypted": false, "metadata_present": false}
```

## gr-linux-crypto integration

Combine with the receive path in
[`gr-linux-crypto-demo.md`](gr-linux-crypto-demo.md):

1. Pull IQ over ZMQ from a remote SDR host.
2. Detect preamble and publish mode ID on PUB (port 5560).
3. A separate process subscribes, retrieves keys via gr-linux-crypto when `encrypted` is true,
   and starts the profile-specific demodulator.

## Endpoint conventions

| Endpoint | Default port / path | Role |
|---|---|---|
| IQ PUSH/PULL | 5555 | Distributed sample streaming (gr-ident profile) |
| Preamble JSON PUB | 5560 | Receive-side decode results |
| TX/PTT control SUB | 5561 | gr-ident profile (multipart JSON/text) |
| LinHT PTT PUB/SUB | `ipc:///tmp/ptt_msg` | LinHT GUI PTT (PMT SOT/EOT) |
| LinHT baseband | `ipc:///tmp/bsb_rx`, `ipc:///tmp/bsb_tx` | LinHT int32 IQ (not gr-ident PUSH/PULL) |

| Parameter | PUSH sink (default) | PULL source (default) |
|---|---|---|
| `bind` | `true` | `false` |

This matches the GNU Radio convention: bind on the sender, connect on the receiver. Override
`bind` when using ZMQ forwarder devices (proxy).

## Related headers

- [`GrIdentZmqBlocks.hpp`](../../blocklib/grident/include/gnuradio-4.0/grident/GrIdentZmqBlocks.hpp)
- Adapted from [gnuradio/gr4-incubator](https://github.com/gnuradio/gr4-incubator) zeromq blocks
