#include <gnuradio/grident/tx_control.h>

#include <algorithm>
#include <cctype>
#include <string>
#include <string_view>

namespace gr {
namespace grident {
namespace {

std::string_view trim(std::string_view value)
{
    while (!value.empty() && std::isspace(static_cast<unsigned char>(value.front()))) {
        value.remove_prefix(1);
    }
    while (!value.empty() && std::isspace(static_cast<unsigned char>(value.back()))) {
        value.remove_suffix(1);
    }
    return value;
}

bool contains_key_true(std::string_view text, std::string_view key)
{
    const std::string needle = std::string("\"") + std::string(key) + "\":true";
    if (text.find(needle) != std::string_view::npos) {
        return true;
    }
    const std::string needle_num = std::string("\"") + std::string(key) + "\":1";
    return text.find(needle_num) != std::string_view::npos;
}

bool contains_key_false(std::string_view text, std::string_view key)
{
    const std::string needle = std::string("\"") + std::string(key) + "\":false";
    if (text.find(needle) != std::string_view::npos) {
        return true;
    }
    const std::string needle_num = std::string("\"") + std::string(key) + "\":0";
    return text.find(needle_num) != std::string_view::npos;
}

tx_control_state parse_linht_pmt_message(const char* data, std::size_t length)
{
    if (data == nullptr || length < 3U) {
        return tx_control_state::unknown;
    }

    if (static_cast<unsigned char>(data[0]) != 0x02U) {
        return tx_control_state::unknown;
    }

    const std::size_t sym_len =
        (static_cast<unsigned char>(data[1]) << 8) | static_cast<unsigned char>(data[2]);
    if (length < 3U + sym_len) {
        return tx_control_state::unknown;
    }

    const std::string_view symbol(data + 3, sym_len);
    if (symbol == "SOT") {
        return tx_control_state::on;
    }
    if (symbol == "EOT") {
        return tx_control_state::off;
    }

    return tx_control_state::unknown;
}

} // namespace

tx_control_state parse_tx_control_message(const char* data, std::size_t length)
{
    if (data == nullptr || length == 0) {
        return tx_control_state::unknown;
    }

    const auto pmt_state = parse_linht_pmt_message(data, length);
    if (pmt_state != tx_control_state::unknown) {
        return pmt_state;
    }

    std::string_view text(data, length);
    text = trim(text);

    if (text.empty()) {
        return tx_control_state::unknown;
    }

    if (text.front() == '{') {
        if (contains_key_true(text, "ptt") || contains_key_true(text, "tx") || contains_key_true(text, "key")) {
            return tx_control_state::on;
        }
        if (contains_key_false(text, "ptt") || contains_key_false(text, "tx") || contains_key_false(text, "key")) {
            return tx_control_state::off;
        }
        return tx_control_state::unknown;
    }

    std::string upper(text);
    std::transform(upper.begin(), upper.end(), upper.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });

    if (upper == "1" || upper == "ON" || upper == "TX" || upper == "PTT" || upper == "PTT_ON" || upper == "KEYDOWN"
        || upper == "KEY_DOWN" || upper == "SOT") {
        return tx_control_state::on;
    }

    if (upper == "0" || upper == "OFF" || upper == "RX" || upper == "PTT_OFF" || upper == "KEYUP"
        || upper == "KEY_UP" || upper == "EOT") {
        return tx_control_state::off;
    }

    return tx_control_state::unknown;
}

} // namespace grident
} // namespace gr
