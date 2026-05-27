/*
 * Golay(24,12) codec — same algorithm as gr-satellites / M17 LICH.
 * Based on R.H. Morelos-Zaragoza, The Art of Error Correcting Coding, Section 2.2.3.
 */

#include <gnuradio/grident/golay24_12.h>

namespace gr {
namespace grident {

namespace {

constexpr int N = 12;

constexpr uint32_t H[N] = { 0x8008ed, 0x4001db, 0x2003b5, 0x100769, 0x80ed1, 0x40da3,
                            0x20b47,  0x1068f,  0x8d1d,   0x4a3b,   0x2477,  0x1ffe };

constexpr uint32_t B(int i) { return H[i] & 0xfff; }

inline int popcount32(uint32_t x) { return __builtin_popcount(x); }

} // namespace

uint32_t golay24_12::encode(uint16_t data_12)
{
    const uint32_t r = data_12 & 0xfff;
    uint32_t s = 0;

    for (int i = 0; i < N; i++) {
        s <<= 1;
        s |= __builtin_parity(H[i] & r);
    }

    return ((0xfff & s) << N) | r;
}

golay_decode_result golay24_12::decode(uint32_t codeword_24)
{
    golay_decode_result result;
    const uint32_t r = codeword_24 & 0xffffff;
    uint16_t s = 0;
    uint16_t q = 0;
    uint32_t e = 0;

    for (int i = 0; i < N; i++) {
        s <<= 1;
        s |= __builtin_parity(H[i] & r);
    }

    if (popcount32(s) <= 3) {
        e = static_cast<uint32_t>(s) << N;
        goto step8;
    }

    for (int i = 0; i < N; i++) {
        if (popcount32(s ^ B(i)) <= 2) {
            e = (s ^ B(i));
            e <<= N;
            e |= 1u << (N - i - 1);
            goto step8;
        }
    }

    for (int i = 0; i < N; i++) {
        q <<= 1;
        q |= __builtin_parity(B(i) & s);
    }

    if (popcount32(q) <= 3) {
        e = q;
        goto step8;
    }

    for (int i = 0; i < N; i++) {
        if (popcount32(q ^ B(i)) <= 2) {
            e = 1u << (2 * N - i - 1);
            e |= q ^ B(i);
            goto step8;
        }
    }

    return result;

step8:
    const uint32_t corrected = r ^ e;
    result.data = corrected & 0xfff;
    result.num_errors = popcount32(e);
    result.valid = true;
    return result;
}

} // namespace grident
} // namespace gr
