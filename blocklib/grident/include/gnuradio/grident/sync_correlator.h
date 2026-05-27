#ifndef INCLUDED_GRIDENT_SYNC_CORRELATOR_H
#define INCLUDED_GRIDENT_SYNC_CORRELATOR_H

#include <complex>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace gr {
namespace grident {

struct sync_correlate_result {
    std::size_t start_sample = 0;
    int bit_errors = 0;
};

/// Sliding CPFSK 4-FSK sync search (4800 sym/s, 48 kHz sample rate).
std::optional<sync_correlate_result> correlate_cpfsk4_sync(
    std::span<const std::complex<float>> samples,
    std::span<const uint8_t> sync_bits,
    float deviation_low_hz,
    float deviation_high_hz,
    int sample_rate_hz = 48000);

std::vector<uint8_t> demodulate_cpfsk4_bits(
    std::span<const std::complex<float>> samples,
    std::size_t start_sample,
    std::size_t num_bits,
    float deviation_low_hz,
    float deviation_high_hz,
    int sample_rate_hz = 48000);

} // namespace grident
} // namespace gr

#endif
