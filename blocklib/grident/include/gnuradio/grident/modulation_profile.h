#ifndef INCLUDED_GRIDENT_MODULATION_PROFILE_H
#define INCLUDED_GRIDENT_MODULATION_PROFILE_H

#include <gnuradio/grident/sync_sequences.h>

#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace gr {
namespace grident {

struct cpfsk4_profile {
    std::string_view         name;
    sync_sequence_view       sync;
    float                    deviation_low_hz;
    float                    deviation_high_hz;
    int                      sample_rate_hz;
    bool                     cpfsk4_preamble = true;
};

std::optional<cpfsk4_profile> cpfsk4_profile_by_name(std::string_view name);
std::optional<cpfsk4_profile> cpfsk4_profile_for_mode_id(std::uint16_t mode_id);

} // namespace grident
} // namespace gr

#endif
