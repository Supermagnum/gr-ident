#include <gnuradio/grident/sync_sequences.h>

#include <array>
#include <stdexcept>

namespace gr {
namespace grident {
namespace {

constexpr std::array<uint8_t, 16> k_sync_nfm = { 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0 };
constexpr std::array<uint8_t, 24> k_sync_c4fm = {
    1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0,
};
constexpr std::array<uint8_t, 24> k_sync_dpmr = {
    1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0,
};
constexpr std::array<uint8_t, 24> k_sync_dmr = {
    1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0,
};
constexpr std::array<uint8_t, 16> k_sync_nxdn = { 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1 };
constexpr std::array<uint8_t, 16> k_sync_m17 = { 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0 };
constexpr std::array<uint8_t, 16> k_sync_dstar = { 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1 };

struct named_sync {
    std::string_view            name;
    std::span<const std::uint8_t> bits;
};

constexpr named_sync k_named_syncs[] = {
    { "sync_nfm", k_sync_nfm },
    { "sync_c4fm", k_sync_c4fm },
    { "sync_dpmr", k_sync_dpmr },
    { "sync_dmr", k_sync_dmr },
    { "sync_nxdn", k_sync_nxdn },
    { "sync_m17", k_sync_m17 },
    { "sync_dstar", k_sync_dstar },
};

} // namespace

sync_sequence_view sync_sequence_by_name(std::string_view name)
{
    for (const auto& entry : k_named_syncs) {
        if (entry.name == name) {
            return sync_sequence_view{ entry.name, entry.bits };
        }
    }
    throw std::invalid_argument("unknown gr-ident sync sequence name");
}

} // namespace grident
} // namespace gr
