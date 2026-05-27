#include <gnuradio/grident/golay24_12.h>
#include <gnuradio/grident/mode_table.h>
#include <gnuradio/grident/preamble_codec.h>
#include <gnuradio/grident/preamble_field.h>

#include <cstdio>
#include <cstdlib>

#define CHECK(cond, msg)                                                                           \
    do {                                                                                           \
        if (!(cond)) {                                                                             \
            std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, msg);                     \
            return EXIT_FAILURE;                                                                   \
        }                                                                                          \
    } while (0)

int main()
{
    const uint16_t samples[] = { 0x000, 0xabc, 0x123, 0x7ff, 0x055 };
    for (uint16_t data : samples) {
        const uint32_t encoded = gr::grident::golay24_12::encode(data);
        auto decoded = gr::grident::golay24_12::decode(encoded);
        CHECK(decoded.valid, "round-trip valid");
        CHECK(decoded.data == (data & 0xfff), "round-trip data");
        CHECK(decoded.num_errors == 0, "round-trip zero errors");
    }

    uint32_t encoded = gr::grident::golay24_12::encode(0x5a5);
    encoded ^= (1u << 3);
    auto corrected = gr::grident::golay24_12::decode(encoded);
    CHECK(corrected.valid, "single-bit flip corrected");
    CHECK(corrected.data == 0x5a5, "single-bit flip data");
    CHECK(corrected.num_errors == 1, "single-bit flip count");

    encoded = gr::grident::golay24_12::encode(0x5a5);
    encoded ^= 0xf;
    auto failed = gr::grident::golay24_12::decode(encoded);
    CHECK(!failed.valid, "four-bit flip uncorrectable");

    gr::grident::preamble_field field{ 120, false, true };
    const uint32_t codeword = gr::grident::encode_preamble(field);
    const auto status = gr::grident::decode_preamble(codeword);
    CHECK(status.golay.valid, "preamble decode valid");
    CHECK(status.field.mode_id == 120, "preamble mode id");
    CHECK(status.field.digital, "preamble digital flag");
    CHECK(!status.field.encrypted, "preamble encrypted flag");

    const auto info = gr::grident::lookup_mode(110);
    CHECK(info.has_value(), "mode lookup EchoLink");
    CHECK(info->name == "EchoLink", "mode name EchoLink");

    std::printf("All golay/preamble tests passed.\n");
    return EXIT_SUCCESS;
}
