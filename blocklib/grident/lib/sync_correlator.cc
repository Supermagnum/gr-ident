#include <gnuradio/grident/sync_correlator.h>

#include <algorithm>
#include <cmath>
#include <complex>
#include <numbers>
#include <vector>

namespace gr {
namespace grident {
namespace {

constexpr int k_symbol_rate = 4800;

int samples_per_symbol(int sample_rate_hz)
{
    return sample_rate_hz / k_symbol_rate;
}

float symbol_frequency(int symbol, float low_hz, float high_hz)
{
    static constexpr float table[4] = { 0.0f, 0.0f, 0.0f, 0.0f };
    (void)table;
    switch (symbol & 0x3) {
    case 0:
        return -high_hz;
    case 1:
        return -low_hz;
    case 2:
        return low_hz;
    default:
        return high_hz;
    }
}

std::vector<int> bits_to_symbols(std::span<const uint8_t> bits)
{
    std::vector<uint8_t> padded(bits.begin(), bits.end());
    if (padded.size() % 2 != 0) {
        padded.push_back(0);
    }
    std::vector<int> symbols;
    symbols.reserve(padded.size() / 2);
    for (std::size_t i = 0; i + 1 < padded.size(); i += 2) {
        symbols.push_back(((padded[i] & 1) << 1) | (padded[i + 1] & 1));
    }
    return symbols;
}

std::vector<int> demodulate_symbols(
    std::span<const std::complex<float>> samples,
    std::size_t start,
    std::size_t num_symbols,
    float low_hz,
    float high_hz,
    int sample_rate_hz)
{
    const int sps = samples_per_symbol(sample_rate_hz);
    std::vector<int> symbols;
    symbols.reserve(num_symbols);
    std::size_t offset = start;

    for (std::size_t sym_idx = 0; sym_idx < num_symbols; ++sym_idx) {
        if (offset + static_cast<std::size_t>(sps) > samples.size()) {
            break;
        }

        float mean_freq = 0.0f;
        for (int i = 1; i < sps; ++i) {
            const auto& curr = samples[offset + static_cast<std::size_t>(i)];
            const auto& prev = samples[offset + static_cast<std::size_t>(i - 1)];
            const float dphase = std::arg(curr * std::conj(prev));
            mean_freq += dphase * static_cast<float>(sample_rate_hz)
                / (2.0f * std::numbers::pi_v<float>);
        }
        mean_freq /= static_cast<float>(std::max(1, sps - 1));

        int best_sym = 0;
        float best_err = std::numeric_limits<float>::max();
        for (int sym = 0; sym < 4; ++sym) {
            const float err = std::abs(mean_freq - symbol_frequency(sym, low_hz, high_hz));
            if (err < best_err) {
                best_err = err;
                best_sym = sym;
            }
        }
        symbols.push_back(best_sym);
        offset += static_cast<std::size_t>(sps);
    }
    return symbols;
}

std::vector<uint8_t> symbols_to_bits(std::span<const int> symbols)
{
    std::vector<uint8_t> bits;
    bits.reserve(symbols.size() * 2);
    for (int sym : symbols) {
        bits.push_back(static_cast<uint8_t>((sym >> 1) & 1));
        bits.push_back(static_cast<uint8_t>(sym & 1));
    }
    return bits;
}

} // namespace

std::optional<sync_correlate_result> correlate_cpfsk4_sync(
    std::span<const std::complex<float>> samples,
    std::span<const uint8_t> sync_bits,
    float deviation_low_hz,
    float deviation_high_hz,
    int sample_rate_hz)
{
    const auto expected = bits_to_symbols(sync_bits);
    if (expected.empty()) {
        return std::nullopt;
    }

    const int sps = samples_per_symbol(sample_rate_hz);
    const std::size_t sync_samples = expected.size() * static_cast<std::size_t>(sps);
    if (samples.size() < sync_samples) {
        return std::nullopt;
    }

    sync_correlate_result best;
    best.bit_errors = static_cast<int>(expected.size());
    bool found = false;

    const std::size_t search = samples.size() - sync_samples + 1;
    for (std::size_t start = 0; start < search; ++start) {
        const auto got = demodulate_symbols(
            samples, start, expected.size(), deviation_low_hz, deviation_high_hz, sample_rate_hz);
        if (got.size() < expected.size()) {
            continue;
        }
        int errors = 0;
        for (std::size_t i = 0; i < expected.size(); ++i) {
            if (got[i] != expected[i]) {
                ++errors;
            }
        }
        if (errors < best.bit_errors) {
            best.start_sample = start;
            best.bit_errors = errors;
            found = true;
            if (errors == 0) {
                break;
            }
        }
    }

    return found ? std::optional<sync_correlate_result>(best) : std::nullopt;
}

std::vector<uint8_t> demodulate_cpfsk4_bits(
    std::span<const std::complex<float>> samples,
    std::size_t start_sample,
    std::size_t num_bits,
    float deviation_low_hz,
    float deviation_high_hz,
    int sample_rate_hz)
{
    const std::size_t num_symbols = (num_bits + 1) / 2;
    const auto symbols = demodulate_symbols(
        samples, start_sample, num_symbols, deviation_low_hz, deviation_high_hz, sample_rate_hz);
    auto bits = symbols_to_bits(symbols);
    if (bits.size() > num_bits) {
        bits.resize(num_bits);
    }
    return bits;
}

} // namespace grident
} // namespace gr
