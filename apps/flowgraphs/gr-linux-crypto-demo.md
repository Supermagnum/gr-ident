# gr-linux-crypto Reference Flowgraph

This document describes a reference GNU Radio 4.x flowgraph that combines gr-ident
preamble detection with [gr-linux-crypto](https://github.com/Supermagnum/gr-linux-crypto)
key retrieval and payload decryption.

It is a design reference. Build and run after installing GNU Radio 4.x, the gr-ident
plugin (`build-gr4/`), and gr-linux-crypto.

## Signal path

```
RF / IQ file
    |
    v
[Channel filter / resample to 48 kHz]
    |
    v
[Profile demod + gr-ident sync correlator]     python/grident/iq_decode.py reference
    |                                          blocklib/grident/lib/preamble_detect.cc
    v
[Golay decode primary preamble]
    |
    +-- bit 10 = 0  ---> [Clear payload demod branch]
    |
    +-- bit 10 = 1  ---> [gr-linux-crypto key retrieve]
                              |
                              v
                         [Decrypt payload (ChaCha20 / AES per policy)]
    |
    v
[Optional metadata decode if bit 9 = 1]
    |
    v
[Mode router -> mode-specific decoder]
```

## GNU Radio 4.x blocks (gr-ident)

| Block | Role |
|---|---|
| `gr::grident::GolayDecode` | Primary (and secondary) Golay codewords |
| `gr::grident::PreambleDecode` | Unpack mode ID and flags |
| `gr::grident::MetadataDecode` | Unpack bandwidth / codec / callsign nibble |
| `gr::grident::PreambleSource` | Transmit-side preamble generation |

IQ-level sync search and CPFSK demodulation are provided by the shared C++ library
(`sync_correlator`, `preamble_detect`) and the Python reference in `iq_decode.py`.
Wire these ahead of the Golay blocks in a flowgraph, or call the library from a custom
GR4 block for your target profile.

For multi-host setups, use the ZeroMQ blocks in `GrIdentZmqBlocks` to pull IQ from a
remote SDR process and publish preamble JSON to subscribers. See
[`zmq-distributed-demo.md`](zmq-distributed-demo.md).

## gr-linux-crypto integration points

1. **After preamble decode** — Read bit 10 (encrypted). If set, invoke gr-linux-crypto
   key retrieval (SSH agent, GPG, or file-based key) before starting the payload FEC.
2. **Metadata field** — When bit 9 is set, decode the secondary Golay codeword with
   `MetadataDecode`. Use `codec_param` and `bandwidth_code` to select the decryption
   profile and filter bandwidth.
3. **Open + signed payload** — When bit 10 = 0, pass audio/data directly; optionally
   verify an Ed25519 signature frame appended after the transmission (gr-linux-crypto
   signing API).

## Example receive sequence (pseudocode)

```python
result = decode_iq_file(Path("capture.cf32"))
if not result or not result.valid:
    return

if result.encrypted:
    key = gr_linux_crypto.retrieve_key(policy="ssh-agent")
    payload = decrypt_stream(key, after_sample=result.preamble_start + preamble_len)
else:
    payload = demod_payload(after_sample=result.preamble_start + preamble_len)

if result.metadata_present and result.metadata:
    apply_bandwidth(result.metadata.bandwidth_code)
```

## Transmit sequence

1. Build `PreambleField` (set `metadata_present` if using secondary metadata).
2. Optionally build `MetadataField` (bandwidth, codec, callsign nibble).
3. Modulate with `ModulationProfile.modulate_preamble()` (Python) or GR4
   `PreambleSource` + `MetadataEncode` + profile modulator blocks.
4. If encrypted, prepend key negotiation per gr-linux-crypto and set bit 10.

## Related documentation

- [Security Integration](../README.md#security-integration--gr-linux-crypto)
- [Gateway integration (VoIP adapters, ZMQ, gr-linux-crypto)](../docs/gateway-integration.md)
- [Optional secondary metadata](../README.md#optional-secondary-metadata-field)
- [Sync sequences](../docs/sync-sequences.md)
- [ZeroMQ protocol](../docs/zeromq-protocol.md)
