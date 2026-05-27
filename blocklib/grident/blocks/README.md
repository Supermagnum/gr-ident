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

## Registered blocks

| Block | Description |
|---|---|
| `gr::grident::GolayEncode` | 12-bit field to Golay(24,12) codeword |
| `gr::grident::GolayDecode` | Golay codeword to 12-bit field |
| `gr::grident::PreambleSource` | Emit configured gr-ident preamble codeword(s) |
| `gr::grident::PreambleDecode` | Codeword to packed preamble field |

Core codec sources are shared with the Meson standalone library in `blocklib/grident/lib/`.

IQ file generation and verification remain in `python/grident/` (no GR runtime required).
