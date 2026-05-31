# gr-ident Testing Guide

This document is the entry point for human testers. It covers prerequisites, smoke tests,
and GNU Radio 4.x flowgraph runners.

## Prerequisites

### All testers (Python IQ path)

| Package | Debian/Ubuntu | Purpose |
|---|---|---|
| Python 3.10+ | `python3` | Reference decode and unit tests |
| Meson, Ninja | `meson ninja-build` | C++ codec library tests |

No GNU Radio install is required for the Python-only path.

### GNU Radio 4.x plugin testers

| Package | Debian/Ubuntu | Purpose |
|---|---|---|
| GNU Radio 4.x | Prebuilt tree or source install | GR4 headers and core libraries |
| GCC 14 | `g++-14` | C++23 build (CMake selects `g++-14` when present) |
| CMake 3.24+ | `cmake` | Builds `GrIdentBlocks` plugin |
| pkg-config | `pkg-config` | Finds system libraries |

Set `CMAKE_PREFIX_PATH` to your GNU Radio 4 install (default in docs: `/opt/gnuradio4-gcc`).

### PTT / ZeroMQ tests

These require the optional `GrIdentZmqBlocks` plugin. Install:

| Package | Debian/Ubuntu | Purpose |
|---|---|---|
| libzmq | `libzmq3-dev` | ZeroMQ C library + headers (cppzmq) |
| pyzmq | `python3-zmq` or `pip install pyzmq` | Python PTT control helpers and tests |

Without `libzmq3-dev`, CMake still builds `GrIdentBlocks` but skips ZMQ blocks and PTT smoke tests.

## Build

### Python + Meson codec library

```bash
meson setup build
meson test -C build
PYTHONPATH=python python3 -m unittest discover -s python/tests -v
```

### GNU Radio 4.x plugin and flowgraph runners

```bash
cmake -B build-gr4 -DCMAKE_PREFIX_PATH=/opt/gnuradio4-gcc
cmake --build build-gr4
ctest --test-dir build-gr4 --output-on-failure
```

Optional install into the GNU Radio prefix:

```bash
cmake --install build-gr4 --prefix /opt/gnuradio4-gcc
```

## Five-minute smoke tests

### 1. Python IQ decode (no GNU Radio)

```bash
PYTHONPATH=python python3 apps/grident_iq_test.py \
  --input python/tests/fixtures/common_modes/mode_110.cf32 \
  --expect-mode-id 110
```

Expected: `mode_id=110`, exit code 0.

### 2. GR4 receive flowgraph (IQ file to preamble detect)

```bash
./build-gr4/grident_receive_flowgraph \
  python/tests/fixtures/common_modes/mode_110.cf32 110
```

Expected: `OK mode_id=110 packed=0x.... sync_start=...`

### 3. GR4 YAML flowgraph runner (reference graphs)

The repository includes reference `.gr.yaml` graphs under `apps/flowgraphs/`. The runner is:

```bash
./build-gr4/grident_run_flowgraph \
  apps/flowgraphs/receive_iq_detect.gr.yaml \
  REPLACE_ME.cf32=python/tests/fixtures/common_modes/mode_110.cf32
```

YAML loading requires a full GNU Radio 4 scheduler graph definition; the checked-in YAML files document block wiring. Use `grident_receive_flowgraph` for automated IQ validation until the YAML importer path is fully exercised in CI.

### 4. PTT / ZeroMQ preamble burst (requires libzmq)

Terminal A (runs the GR4-side subscriber and preamble gate):

```bash
./build-gr4/grident_ptt_zmq_smoke
```

This binary binds `tcp://127.0.0.1:5562`, exercises both **grident** (multipart JSON/text)
and **linht** (PMT SOT/EOT) profiles, and prints the Golay preamble codeword on key-down.
Expected final line: `PTT/ZMQ smoke test OK`.

Terminal B (optional manual PTT publish on a live LinHT stack):

```python
from grident.tx_control import TxControlState, send_tx_control

# LinHT GUI path (default profile)
send_tx_control("ipc:///tmp/ptt_msg", TxControlState.ON)
send_tx_control("ipc:///tmp/ptt_msg", TxControlState.OFF)

# gr-ident standalone profile
send_tx_control("tcp://127.0.0.1:5561", TxControlState.ON, profile="grident")
send_tx_control("tcp://127.0.0.1:5561", TxControlState.OFF, profile="grident")
```

Use a separate process only when not running `grident_ptt_zmq_smoke` (that test publishes PTT internally).

## Registered GR4 blocks (test-relevant)

| Block | Role |
|---|---|
| `gr::grident::IqCf32FileSource` | Read `.cf32` IQ captures |
| `gr::grident::Cpfsk4SyncCorrelator` | Sync search on CPFSK 4-FSK profiles |
| `gr::grident::Cpfsk4PreambleDetect` | Full IQ preamble detect + Golay decode |
| `gr::grident::PreambleOnPtt` | Emit preamble burst on PTT key-down |
| `gr::grident::zeromq::ZmqTxControlSub` | SUB socket for PTT/TX commands |

See [`blocklib/grident/blocks/README.md`](blocklib/grident/blocks/README.md) for the full block list.

## Runnable flowgraphs

| File | Description |
|---|---|
| [`apps/flowgraphs/receive_iq_detect.gr.yaml`](apps/flowgraphs/receive_iq_detect.gr.yaml) | IQ file to CPFSK preamble detect |
| [`apps/flowgraphs/ptt_preamble.gr.yaml`](apps/flowgraphs/ptt_preamble.gr.yaml) | ZMQ PTT to gated preamble (needs external PTT publisher) |

Run with `grident_run_flowgraph` and `key=value` substitutions for paths and parameters.

## Regenerate test documentation

```bash
PYTHONPATH=python python3 python/grident/generate_docs.py
```

Requires ImageMagick (`convert`) for PNG waterfalls.

## Signal validation (radio-modulation-validator)

`grident-validate` runs two-layer validation on committed IQ test vectors:

```bash
PYTHONPATH=python python3 apps/grident_validate.py \
  --fixtures python/tests/fixtures/common_modes/
```

Requires [radio-modulation-validator](https://github.com/Supermagnum/radio-modulation-validator)
installed at `../radio-modulation-validator/` or on `PATH`. Preamble-only validation runs without it:

```bash
PYTHONPATH=python python3 apps/grident_validate.py --preamble-only
```

Results are written to `docs/validation-report.md`. See [`docs/rmv-integration.md`](docs/rmv-integration.md).

## Known limits

- `Cpfsk4PreambleDetect` and `Cpfsk4SyncCorrelator` apply to **CPFSK 4-FSK** profiles only (modes such as 20, 104, 110). PSK31 and RTTY use different air interfaces; use the Python `iq_decode.py` path for those modes.
- YAML flowgraphs are minimal reference graphs; use `grident_receive_flowgraph` and `grident_ptt_zmq_smoke` for automated regression.
- The specification has not been reviewed by professional RF engineers; see the README disclaimer before on-air use.
