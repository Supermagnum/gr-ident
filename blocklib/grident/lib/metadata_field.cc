#include <gnuradio/grident/golay24_12.h>
#include <gnuradio/grident/metadata_field.h>

namespace gr {
namespace grident {

uint16_t pack_metadata_field(const metadata_field& field)
{
    return (static_cast<uint16_t>(field.bandwidth_code & 0x0f) << 8)
        | (static_cast<uint16_t>(field.codec_param & 0x0f) << 4)
        | static_cast<uint16_t>(field.callsign_nibble & 0x0f);
}

metadata_field unpack_metadata_field(uint16_t raw_12)
{
    metadata_field field;
    field.bandwidth_code = static_cast<uint8_t>((raw_12 >> 8) & 0x0f);
    field.codec_param = static_cast<uint8_t>((raw_12 >> 4) & 0x0f);
    field.callsign_nibble = static_cast<uint8_t>(raw_12 & 0x0f);
    return field;
}

uint32_t encode_metadata(const metadata_field& field)
{
    return golay24_12::encode(pack_metadata_field(field));
}

metadata_field decode_metadata_field(uint32_t codeword_24, bool& valid)
{
    const auto result = golay24_12::decode(codeword_24);
    valid = result.valid;
    if (!result.valid) {
        return {};
    }
    return unpack_metadata_field(result.data);
}

} // namespace grident
} // namespace gr
