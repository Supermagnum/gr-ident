"""Golay(24,12) codec matching the C++ implementation."""

from __future__ import annotations

N = 12

H = (
    0x8008ED,
    0x4001DB,
    0x2003B5,
    0x100769,
    0x80ED1,
    0x40DA3,
    0x20B47,
    0x1068F,
    0x8D1D,
    0x4A3B,
    0x2477,
    0x1FFE,
)


def _parity(value: int) -> int:
    return bin(value & 0xFFFFFFFF).count("1") & 1


def _b(index: int) -> int:
    return H[index] & 0xFFF


def encode_golay24(data_12: int) -> int:
    r = data_12 & 0xFFF
    s = 0
    for i in range(N):
        s = (s << 1) | _parity(H[i] & r)
    return ((s & 0xFFF) << N) | r


def decode_golay24(codeword_24: int) -> tuple[int, int, bool]:
    r = codeword_24 & 0xFFFFFF
    s = 0
    for i in range(N):
        s = (s << 1) | _parity(H[i] & r)

    if bin(s).count("1") <= 3:
        e = s << N
        return _finish(r, e)

    for i in range(N):
        if bin(s ^ _b(i)).count("1") <= 2:
            e = (s ^ _b(i)) << N
            e |= 1 << (N - i - 1)
            return _finish(r, e)

    q = 0
    for i in range(N):
        q = (q << 1) | _parity(_b(i) & s)

    if bin(q).count("1") <= 3:
        return _finish(r, q)

    for i in range(N):
        if bin(q ^ _b(i)).count("1") <= 2:
            e = (1 << (2 * N - i - 1)) | (q ^ _b(i))
            return _finish(r, e)

    return 0, -1, False


def _finish(r: int, e: int) -> tuple[int, int, bool]:
    corrected = r ^ e
    return corrected & 0xFFF, bin(e).count("1"), True
