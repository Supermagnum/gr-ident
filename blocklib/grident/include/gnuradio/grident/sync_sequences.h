#ifndef INCLUDED_GRIDENT_SYNC_SEQUENCES_H
#define INCLUDED_GRIDENT_SYNC_SEQUENCES_H

#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace gr {
namespace grident {

struct sync_sequence_view {
    std::string_view name;
    std::span<const uint8_t> bits;
};

sync_sequence_view sync_sequence_by_name(std::string_view name);

} // namespace grident
} // namespace gr

#endif
