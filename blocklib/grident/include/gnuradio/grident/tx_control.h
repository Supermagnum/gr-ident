#ifndef INCLUDED_GRIDENT_TX_CONTROL_H
#define INCLUDED_GRIDENT_TX_CONTROL_H

#include <cstddef>

namespace gr {
namespace grident {

enum class tx_control_state : unsigned char {
    unknown = 0,
    off     = 1,
    on      = 2,
};

/// LinHT GUI / flowgraph PTT PUB endpoint (see M17-Project/LinHT-utils zmq_proxy).
inline constexpr const char* linht_ptt_endpoint     = "ipc:///tmp/ptt_msg";
/// LinHT flowgraph auxiliary message SUB bind point (SOT/EOT from GUI).
inline constexpr const char* linht_fg_aux_endpoint = "ipc:///tmp/fg_aux_data_in";

/// Parse a ZeroMQ TX/PTT control payload.
/// Supports LinHT GNU Radio PMT strings (SOT/EOT), gr-ident JSON/plain text, and plain SOT/EOT.
tx_control_state parse_tx_control_message(const char* data, std::size_t length);

} // namespace grident
} // namespace gr

#endif
