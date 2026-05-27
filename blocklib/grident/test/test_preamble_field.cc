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
    gr::grident::preamble_field field{ 103, true, true };
    const uint16_t raw = gr::grident::pack_preamble_field(field);
    CHECK(raw == 0x0c67, "packed field value");

    const auto restored = gr::grident::unpack_preamble_field(raw);
    CHECK(restored.mode_id == 103, "restored mode id");
    CHECK(restored.encrypted, "restored encrypted");
    CHECK(restored.digital, "restored digital");

    gr::grident::preamble_field analog{ 20, false, false };
    const uint16_t analog_raw = gr::grident::pack_preamble_field(analog);
    CHECK(analog_raw == 20, "analog packed value");

    std::printf("All preamble field tests passed.\n");
    return EXIT_SUCCESS;
}
