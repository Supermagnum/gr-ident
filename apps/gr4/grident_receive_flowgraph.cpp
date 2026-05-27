#include <gnuradio/grident/modulation_profile.h>
#include <gnuradio/grident/preamble_codec.h>
#include <gnuradio/grident/preamble_detect.h>
#include <gnuradio/grident/preamble_field.h>

#include <complex>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <print>
#include <string>
#include <vector>

namespace {

using gr::grident::cpfsk4_profile_for_mode_id;
using gr::grident::detect_cpfsk4_preamble;
using gr::grident::pack_preamble_field;

std::vector<std::complex<float>> read_cf32(const std::string& path)
{
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("cannot open " + path);
    }

    input.seekg(0, std::ios::end);
    const auto bytes = input.tellg();
    input.seekg(0, std::ios::beg);

    std::vector<std::complex<float>> samples(static_cast<std::size_t>(bytes) / sizeof(std::complex<float>));
    if (!input.read(reinterpret_cast<char*>(samples.data()), bytes)) {
        throw std::runtime_error("read failed for " + path);
    }
    return samples;
}

int run_receive(const std::string& iq_path, std::uint16_t mode_id)
{
    const auto profile = cpfsk4_profile_for_mode_id(mode_id);
    if (!profile) {
        std::println(stderr, "No CPFSK profile for mode_id {}", mode_id);
        return EXIT_FAILURE;
    }

    const auto samples = read_cf32(iq_path);
    const auto result  = detect_cpfsk4_preamble(
        samples,
        profile->sync.bits,
        profile->deviation_low_hz,
        profile->deviation_high_hz,
        profile->sample_rate_hz);

    if (!result.valid) {
        std::println(stderr, "Preamble detect failed for {}", iq_path);
        return EXIT_FAILURE;
    }
    if (result.field.mode_id != mode_id) {
        std::println(
            stderr,
            "Expected mode_id {} got {}",
            mode_id,
            result.field.mode_id);
        return EXIT_FAILURE;
    }

    std::println(
        "OK mode_id={} packed=0x{:04x} sync_start={}",
        result.field.mode_id,
        pack_preamble_field(result.field),
        result.sync_start);
    return EXIT_SUCCESS;
}

} // namespace

int main(int argc, char** argv)
{
    if (argc != 3) {
        std::println(stderr, "Usage: {} <iq.cf32> <mode_id>", argv[0]);
        return EXIT_FAILURE;
    }

    try {
        const std::string iq_path = argv[1];
        const auto        mode_id = static_cast<std::uint16_t>(std::strtoul(argv[2], nullptr, 0));
        return run_receive(iq_path, mode_id);
    } catch (const std::exception& ex) {
        std::println(stderr, "{}", ex.what());
        return EXIT_FAILURE;
    }
}
