#include <gnuradio/grident/metadata_field.h>

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
    gr::grident::metadata_field field{ 3, 5, 0xA };
    const uint16_t raw = gr::grident::pack_metadata_field(field);
    CHECK(raw == 0x035A, "packed metadata value");

    const auto restored = gr::grident::unpack_metadata_field(raw);
    CHECK(restored.bandwidth_code == 3, "bandwidth");
    CHECK(restored.codec_param == 5, "codec");
    CHECK(restored.callsign_nibble == 0xA, "callsign nibble");

    const uint32_t codeword = gr::grident::encode_metadata(field);
    bool valid = false;
    const auto decoded = gr::grident::decode_metadata_field(codeword, valid);
    CHECK(valid, "golay valid");
    CHECK(decoded.bandwidth_code == 3, "decoded bandwidth");

    std::printf("All metadata field tests passed.\n");
    return EXIT_SUCCESS;
}
