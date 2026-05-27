#include <gnuradio/grident/preamble_field.h>
#include <stdexcept>

namespace gr {
namespace grident {

uint16_t pack_preamble_field(const preamble_field& field)
{
    if (field.mode_id > 511) {
        throw std::out_of_range("mode_id exceeds 9-bit range");
    }

    uint16_t raw = field.mode_id & 0x1ff;
    if (field.metadata_present) {
        raw |= (1u << 9);
    }
    if (field.encrypted) {
        raw |= (1u << 10);
    }
    if (field.digital) {
        raw |= (1u << 11);
    }
    return raw;
}

preamble_field unpack_preamble_field(uint16_t raw_12, bool strict_reserved)
{
    const bool metadata_present = (raw_12 >> 9) & 0x1;
    if (strict_reserved && metadata_present) {
        throw std::invalid_argument("metadata bit set but strict_reserved=true");
    }

    preamble_field field;
    field.mode_id = raw_12 & 0x1ff;
    field.metadata_present = metadata_present;
    field.encrypted = (raw_12 >> 10) & 0x1;
    field.digital = (raw_12 >> 11) & 0x1;
    return field;
}

} // namespace grident
} // namespace gr
