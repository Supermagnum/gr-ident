#ifndef INCLUDED_GRIDENT_MODE_TABLE_H
#define INCLUDED_GRIDENT_MODE_TABLE_H

#include <cstdint>
#include <optional>
#include <string_view>

namespace gr {
namespace grident {

struct mode_info {
    std::string_view name;
    bool digital;
    std::string_view category;
};

std::optional<mode_info> lookup_mode(uint16_t mode_id);
const char* mode_name(uint16_t mode_id);

} // namespace grident
} // namespace gr

#endif
