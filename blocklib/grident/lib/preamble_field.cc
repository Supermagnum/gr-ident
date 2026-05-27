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
    if (strict_reserved && ((raw_12 >> 9) & 0x1)) {
        throw std::invalid_argument("reserved preamble bit 9 must be zero");
    }

    preamble_field field;
    field.mode_id = raw_12 & 0x1ff;
    field.encrypted = (raw_12 >> 10) & 0x1;
    field.digital = (raw_12 >> 11) & 0x1;
    return field;
}

} // namespace grident
} // namespace gr
