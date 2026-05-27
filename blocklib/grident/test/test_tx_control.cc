#include <gnuradio/grident/tx_control.h>

#include <cassert>
#include <cstring>

using gr::grident::parse_tx_control_message;
using gr::grident::tx_control_state;

int main()
{
    assert(parse_tx_control_message("PTT_ON", 6) == tx_control_state::on);
    assert(parse_tx_control_message("ptt_off", 7) == tx_control_state::off);
    assert(parse_tx_control_message("TX", 2) == tx_control_state::on);
    assert(parse_tx_control_message("RX", 2) == tx_control_state::off);
    assert(parse_tx_control_message("1", 1) == tx_control_state::on);
    assert(parse_tx_control_message("0", 1) == tx_control_state::off);
    assert(parse_tx_control_message(R"({"ptt":true})", 12) == tx_control_state::on);
    assert(parse_tx_control_message(R"({"ptt":false})", 13) == tx_control_state::off);
    assert(parse_tx_control_message(R"({"tx":1})", 8) == tx_control_state::on);
    assert(parse_tx_control_message("UNKNOWN", 7) == tx_control_state::unknown);

    static constexpr unsigned char k_sot[] = { 0x02, 0x00, 0x03, 'S', 'O', 'T' };
    static constexpr unsigned char k_eot[] = { 0x02, 0x00, 0x03, 'E', 'O', 'T' };
    assert(parse_tx_control_message(reinterpret_cast<const char*>(k_sot), sizeof(k_sot)) == tx_control_state::on);
    assert(parse_tx_control_message(reinterpret_cast<const char*>(k_eot), sizeof(k_eot)) == tx_control_state::off);
    assert(parse_tx_control_message("SOT", 3) == tx_control_state::on);
    assert(parse_tx_control_message("EOT", 3) == tx_control_state::off);
    return 0;
}
