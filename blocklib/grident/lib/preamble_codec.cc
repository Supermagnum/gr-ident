#include <gnuradio/grident/preamble_codec.h>

namespace gr {
namespace grident {

uint32_t encode_preamble(const preamble_field& field)
{
    return golay24_12::encode(pack_preamble_field(field));
}

preamble_decode_status decode_preamble(uint32_t codeword_24)
{
    preamble_decode_status status;
    status.golay = golay24_12::decode(codeword_24);
    if (!status.golay.valid) {
        return status;
    }
    status.field = unpack_preamble_field(status.golay.data);
    return status;
}

std::vector<uint8_t> codeword_to_bits_msb_first(uint32_t codeword_24)
{
    std::vector<uint8_t> bits(24);
    for (int i = 0; i < 24; ++i) {
        bits[i] = (codeword_24 >> (23 - i)) & 1;
    }
    return bits;
}

uint32_t bits_msb_first_to_codeword(const uint8_t* bits, std::size_t nbits)
{
    uint32_t codeword = 0;
    const std::size_t count = nbits < 24 ? nbits : 24;
    for (std::size_t i = 0; i < count; ++i) {
        codeword = (codeword << 1) | (bits[i] & 1);
    }
    for (std::size_t i = count; i < 24; ++i) {
        codeword <<= 1;
    }
    return codeword;
}

} // namespace grident
} // namespace gr
