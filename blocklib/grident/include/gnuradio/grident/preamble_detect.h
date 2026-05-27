#ifndef INCLUDED_GRIDENT_PREAMBLE_DETECT_H
#define INCLUDED_GRIDENT_PREAMBLE_DETECT_H

#include <gnuradio/grident/metadata_field.h>
#include <gnuradio/grident/preamble_field.h>

#include <complex>
#include <cstddef>
#include <span>
#include <vector>

namespace gr {
namespace grident {

struct preamble_detect_result {
    preamble_field field;
    metadata_field metadata;
    bool valid = false;
    bool metadata_valid = false;
    int golay_errors = 0;
    std::size_t sync_start = 0;
    std::size_t preamble_start = 0;
    uint32_t primary_codeword = 0;
    uint32_t metadata_codeword = 0;
};

/// IQ-level CPFSK 4-FSK preamble detector for gr-ident test vectors.
preamble_detect_result detect_cpfsk4_preamble(
    std::span<const std::complex<float>> samples,
    std::span<const uint8_t> sync_bits,
    float deviation_low_hz,
    float deviation_high_hz,
    int sample_rate_hz = 48000);

} // namespace grident
} // namespace gr

#endif
