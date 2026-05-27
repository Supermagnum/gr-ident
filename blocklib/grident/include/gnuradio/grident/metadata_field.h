#ifndef INCLUDED_GRIDENT_METADATA_FIELD_H
#define INCLUDED_GRIDENT_METADATA_FIELD_H

#include <cstdint>

namespace gr {
namespace grident {

struct metadata_field {
    uint8_t bandwidth_code = 0;
    uint8_t codec_param = 0;
    uint8_t callsign_nibble = 0;
};

constexpr uint8_t bandwidth_unspecified = 0;
constexpr uint8_t bandwidth_6_25_khz = 1;
constexpr uint8_t bandwidth_8_33_khz = 2;
constexpr uint8_t bandwidth_12_5_khz = 3;
constexpr uint8_t bandwidth_20_khz = 4;
constexpr uint8_t bandwidth_25_khz = 5;
constexpr uint8_t bandwidth_wfm = 6;

uint16_t pack_metadata_field(const metadata_field& field);
metadata_field unpack_metadata_field(uint16_t raw_12);

uint32_t encode_metadata(const metadata_field& field);
metadata_field decode_metadata_field(uint32_t codeword_24, bool& valid);

} // namespace grident
} // namespace gr

#endif
