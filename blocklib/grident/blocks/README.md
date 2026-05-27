# GNU Radio 4.x blocks

Build the gr-ident plugin for GNU Radio 4.x (header-template blocks + shared plugin):

```bash
cmake -B build-gr4 -DCMAKE_PREFIX_PATH=/opt/gnuradio4-gcc
cmake --build build-gr4
ctest --test-dir build-gr4 --output-on-failure
```

Install (optional):

```bash
cmake --install build-gr4 --prefix /opt/gnuradio4-gcc
```

Requires `libzmq3-dev` (and cppzmq headers) for ZeroMQ blocks.

## Registered blocks (GrIdentBlocks)

| Block | Description |
|---|---|
| `gr::grident::GolayEncode` | 12-bit field to Golay(24,12) codeword |
| `gr::grident::GolayDecode` | Golay codeword to 12-bit field |
| `gr::grident::PreambleSource` | Emit configured gr-ident preamble codeword(s) |
| `gr::grident::PreambleOnPtt` | Emit preamble burst on PTT key-down (tx_in stream) |
| `gr::grident::PreambleDecode` | Codeword to packed preamble field |
| `gr::grident::MetadataEncode` | Secondary metadata to Golay codeword |
| `gr::grident::MetadataDecode` | Metadata codeword to packed 12-bit field |

## IQ demod blocks (GrIdentBlocks)

| Block | Description |
|---|---|
| `gr::grident::IqCf32FileSource` | Read interleaved complex float32 `.cf32` captures |
| `gr::grident::Cpfsk4SyncCorrelator` | CPFSK 4-FSK sync correlator |
| `gr::grident::Cpfsk4PreambleDetect` | IQ-level preamble detect and Golay decode |
| `gr::grident::PreambleDetectConsoleSink` | Print detect strobes (optional) |

CPFSK blocks apply to 4800 sym/s profiles (NFM, C4FM, dPMR, etc.). PSK31/RTTY remain in the Python reference path.

## Runnable flowgraph tools

Built under `build-gr4/` when CMake apps are enabled:

| Binary | Purpose |
|---|---|
| `grident_receive_flowgraph` | IQ `.cf32` file through `Cpfsk4PreambleDetect` |
| `grident_run_flowgraph` | Load and run `.gr.yaml` flowgraphs |
| `grident_ptt_zmq_smoke` | End-to-end PTT/ZMQ preamble burst test (requires libzmq) |

See [`TESTING.md`](../../TESTING.md) and [`apps/flowgraphs/`](../../apps/flowgraphs/).

## ZeroMQ blocks (GrIdentZmqBlocks)

Built when `libzmq` is found by CMake.

| Block | Description |
|---|---|
| `gr::grident::zeromq::ZmqPushSink<T>` | PUSH IQ or scalar streams to a remote flowgraph |
| `gr::grident::zeromq::ZmqPullSource<T>` | PULL IQ or scalar streams from a remote PUSH |
| `gr::grident::zeromq::PreambleResultZmqPub` | PUB JSON preamble decode results |
| `gr::grident::zeromq::ZmqTxControlSub` | SUB TX/PTT control (LinHT PMT SOT/EOT or grident JSON/text); drives `PreambleOnPtt` |

See [`apps/flowgraphs/zmq-distributed-demo.md`](../../apps/flowgraphs/zmq-distributed-demo.md).

## C++ library (IQ-level)

| Component | Header | Role |
|---|---|---|
| Sync correlator | `sync_correlator.h` | CPFSK 4-FSK sync search |
| Preamble detect | `preamble_detect.h` | IQ capture to mode ID + optional metadata |

Use these from custom GR4 blocks or standalone tools. Python reference:
`python/grident/iq_decode.py`.

## Reference flowgraphs

- [gr-linux-crypto integration demo](../../apps/flowgraphs/gr-linux-crypto-demo.md)
- [ZeroMQ distributed demo](../../apps/flowgraphs/zmq-distributed-demo.md)

Core codec sources are shared with the Meson standalone library in `blocklib/grident/lib/`.

IQ file generation and verification remain in `python/grident/` (no GR runtime required).
