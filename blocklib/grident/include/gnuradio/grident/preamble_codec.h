#ifndef INCLUDED_GRIDENT_PREAMBLE_CODEC_H
#define INCLUDED_GRIDENT_PREAMBLE_CODEC_H

#include <gnuradio/grident/golay24_12.h>
#include <gnuradio/grident/preamble_field.h>

#include <cstdint>
#include <vector>

namespace gr {
namespace grident {

struct preamble_decode_status {
    preamble_field field;
    golay_decode_result golay;
};

uint32_t encode_preamble(const preamble_field& field);
preamble_decode_status decode_preamble(uint32_t codeword_24);

std::vector<uint8_t> codeword_to_bits_msb_first(uint32_t codeword_24);
uint32_t bits_msb_first_to_codeword(const uint8_t* bits, std::size_t nbits);

} // namespace grident
} // namespace gr

#endif
