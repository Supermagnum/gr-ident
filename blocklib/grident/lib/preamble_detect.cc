#include <gnuradio/grident/preamble_codec.h>
#include <gnuradio/grident/preamble_detect.h>
#include <gnuradio/grident/sync_correlator.h>

namespace gr {
namespace grident {
namespace {

uint32_t bits_to_codeword(std::span<const uint8_t> bits)
{
    std::vector<uint8_t> padded(bits.begin(), bits.end());
    while (padded.size() < 24) {
        padded.push_back(0);
    }
    return bits_msb_first_to_codeword(padded.data(), 24);
}

} // namespace

preamble_detect_result detect_cpfsk4_preamble(
    std::span<const std::complex<float>> samples,
    std::span<const uint8_t> sync_bits,
    float deviation_low_hz,
    float deviation_high_hz,
    int sample_rate_hz)
{
    preamble_detect_result out;

    const auto sync = correlate_cpfsk4_sync(
        samples, sync_bits, deviation_low_hz, deviation_high_hz, sample_rate_hz);
    if (!sync.has_value()) {
        return out;
    }

    out.sync_start = sync->start_sample;
    const int sps = sample_rate_hz / 4800;
    const std::size_t sync_symbols = (sync_bits.size() + 1) / 2;
    out.preamble_start = out.sync_start + sync_symbols * static_cast<std::size_t>(sps);

    const auto primary_bits = demodulate_cpfsk4_bits(
        samples, out.preamble_start, 24, deviation_low_hz, deviation_high_hz, sample_rate_hz);
    out.primary_codeword = bits_to_codeword(primary_bits);

    const auto status = decode_preamble(out.primary_codeword);
    out.field = status.field;
    out.golay_errors = status.golay.num_errors;
    out.valid = status.golay.valid;

    if (out.valid && out.field.metadata_present) {
        const auto meta_bits = demodulate_cpfsk4_bits(
            samples,
            out.preamble_start,
            48,
            deviation_low_hz,
            deviation_high_hz,
            sample_rate_hz);
        if (meta_bits.size() >= 48) {
            std::vector<uint8_t> secondary(meta_bits.begin() + 24, meta_bits.begin() + 48);
            out.metadata_codeword = bits_to_codeword(secondary);
            out.metadata = decode_metadata_field(out.metadata_codeword, out.metadata_valid);
            out.valid = out.valid && out.metadata_valid;
        } else {
            out.valid = false;
        }
    }

    return out;
}

} // namespace grident
} // namespace gr
