#ifndef INCLUDED_GRIDENT_PREAMBLE_FIELD_H
#define INCLUDED_GRIDENT_PREAMBLE_FIELD_H

#include <cstdint>

namespace gr {
namespace grident {

struct preamble_field {
    uint16_t mode_id = 0;
    bool encrypted = false;
    bool digital = false;
    bool metadata_present = false;
};

uint16_t pack_preamble_field(const preamble_field& field);
preamble_field unpack_preamble_field(uint16_t raw_12, bool strict_reserved = true);

} // namespace grident
} // namespace gr

#endif
