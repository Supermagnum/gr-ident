#ifndef GNURADIO_GRIDENT_IQ_BLOCKS_HPP
#define GNURADIO_GRIDENT_IQ_BLOCKS_HPP

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/annotated.hpp>
#include <gnuradio-4.0/meta/reflection.hpp>

#include <gnuradio/grident/modulation_profile.h>
#include <gnuradio/grident/preamble_codec.h>
#include <gnuradio/grident/preamble_detect.h>
#include <gnuradio/grident/preamble_field.h>
#include <gnuradio/grident/sync_correlator.h>

#include <complex>
#include <cstdio>
#include <format>
#include <fstream>
#include <vector>

namespace gr::grident {

GR_REGISTER_BLOCK("gr::grident::IqCf32FileSource", gr::grident::IqCf32FileSource)

struct IqCf32FileSource : Block<IqCf32FileSource> {
    using Description = Doc<R""(@brief Read interleaved IQ float32 samples from a binary .cf32 file.

Output sample type is std::complex<float>. Stops after one pass unless repeat is true.)"">;

    PortOut<std::complex<float>> out;

    Annotated<std::string, "path", Visible, Doc<"Path to raw IQ file (complex float32 LE)">> path;
    Annotated<bool, "repeat", Visible, Doc<"Repeat file from start when EOF is reached">> repeat = false;

    GR_MAKE_REFLECTABLE(IqCf32FileSource, out, path, repeat);

    std::vector<std::complex<float>> _samples;
    std::size_t                       _index = 0U;

    void start()
    {
        _index = 0U;
        _samples.clear();

        std::ifstream input(path, std::ios::binary);
        if (!input) {
            throw gr::exception(std::format("IqCf32FileSource: cannot open '{}'", static_cast<std::string>(path)));
        }

        input.seekg(0, std::ios::end);
        const auto bytes = input.tellg();
        input.seekg(0, std::ios::beg);
        if (bytes <= 0) {
            throw gr::exception(std::format("IqCf32FileSource: empty file '{}'", static_cast<std::string>(path)));
        }

        const std::size_t count = static_cast<std::size_t>(bytes) / sizeof(std::complex<float>);
        _samples.resize(count);
        if (!input.read(reinterpret_cast<char*>(_samples.data()), static_cast<std::streamsize>(bytes))) {
            throw gr::exception(std::format("IqCf32FileSource: read failed for '{}'", static_cast<std::string>(path)));
        }
    }

    [[nodiscard]] work::Status processBulk(OutputSpanLike auto& outputSpan)
    {
        if (_samples.empty()) {
            outputSpan.publish(0U);
            return work::Status::DONE;
        }

        const std::size_t nOut = outputSpan.size();
        std::size_t       published = 0U;
        for (std::size_t i = 0; i < nOut; ++i) {
            if (_index >= _samples.size()) {
                if (!repeat) {
                    break;
                }
                _index = 0U;
            }
            outputSpan[published++] = _samples[_index++];
        }

        outputSpan.publish(published);
        if (published == 0U && !repeat) {
            return work::Status::DONE;
        }
        return published > 0U ? work::Status::OK : work::Status::INSUFFICIENT_OUTPUT_ITEMS;
    }
};

GR_REGISTER_BLOCK("gr::grident::Cpfsk4SyncCorrelator", gr::grident::Cpfsk4SyncCorrelator)

struct Cpfsk4SyncCorrelator : Block<Cpfsk4SyncCorrelator> {
    using Description = Doc<R""(@brief CPFSK 4-FSK sync correlator for gr-ident air interfaces.

Buffers IQ input and searches for the profile sync sequence. Emits a one-sample strobe on
sync_found when correlation succeeds. Diagnostic fields sync_start and bit_errors are updated.)"">;

    PortIn<std::complex<float>> in;
    PortOut<uint8_t>              sync_found;

    Annotated<uint16_t, "mode_id", Visible, Doc<"Mode ID used to select sync/deviation profile (0 = use profile name)">> mode_id = 0U;
    Annotated<std::string, "profile", Visible, Doc<"Profile name when mode_id is 0">> profile = "nfm_125_4800";
    Annotated<std::size_t, "sync_start", Doc<"Sample index of detected sync (diagnostic)">> sync_start = 0U;
    Annotated<int, "bit_errors", Doc<"Sync bit errors at detection (diagnostic)">> bit_errors = -1;

    GR_MAKE_REFLECTABLE(Cpfsk4SyncCorrelator, in, sync_found, mode_id, profile, sync_start, bit_errors);

    std::vector<std::complex<float>> _buffer;
    bool                             _found = false;

    [[nodiscard]] cpfsk4_profile active_profile() const
    {
        if (mode_id != 0U) {
            if (auto resolved = cpfsk4_profile_for_mode_id(mode_id)) {
                return *resolved;
            }
            throw gr::exception(std::format("Cpfsk4SyncCorrelator: no CPFSK profile for mode_id {}", mode_id));
        }
        if (auto resolved = cpfsk4_profile_by_name(profile)) {
            return *resolved;
        }
        throw gr::exception(std::format("Cpfsk4SyncCorrelator: unknown profile '{}'", static_cast<std::string>(profile)));
    }

    void try_detect()
    {
        if (_found || _buffer.size() < 48000U) {
            return;
        }

        const auto params = active_profile();
        const auto result = correlate_cpfsk4_sync(
            _buffer,
            params.sync.bits,
            params.deviation_low_hz,
            params.deviation_high_hz,
            params.sample_rate_hz);
        if (!result.has_value()) {
            return;
        }

        _found      = true;
        sync_start  = result->start_sample;
        bit_errors  = result->bit_errors;
    }

    [[nodiscard]] work::Status processBulk(InputSpanLike auto& inputSpan, OutputSpanLike auto& outputSpan)
    {
        const std::size_t nIn = inputSpan.size();
        _buffer.insert(_buffer.end(), inputSpan.begin(), inputSpan.end());
        try_detect();

        const std::size_t nOut = outputSpan.size();
        std::size_t       published = 0U;
        for (std::size_t i = 0; i < nOut && i < nIn; ++i) {
            const bool strobe = _found && (i + 1U == nIn) && sync_start + 4800U <= _buffer.size();
            outputSpan[published++] = strobe ? static_cast<uint8_t>(1) : static_cast<uint8_t>(0);
        }
        outputSpan.publish(published);
        return published > 0U ? work::Status::OK : work::Status::INSUFFICIENT_OUTPUT_ITEMS;
    }
};

GR_REGISTER_BLOCK("gr::grident::Cpfsk4PreambleDetect", gr::grident::Cpfsk4PreambleDetect)

struct Cpfsk4PreambleDetect : Block<Cpfsk4PreambleDetect> {
    using Description = Doc<R""(@brief IQ-level CPFSK 4-FSK gr-ident preamble detector.

Buffers IQ, runs sync search and Golay decode for the selected profile/mode_id, and emits a
one-sample strobe on detect_strobe when successful. Updates detected_mode_id and packed_preamble.)"">;

    PortIn<std::complex<float>> in;
    PortOut<uint8_t>              detect_strobe;

    Annotated<uint16_t, "mode_id", Visible, Doc<"Expected mode ID (selects profile; 0 uses profile name)">> mode_id = 110U;
    Annotated<std::string, "profile", Visible, Doc<"Profile name when mode_id is 0">> profile = "nfm_125_4800";
    Annotated<bool, "valid", Doc<"True after successful detect">> valid = false;
    Annotated<uint16_t, "detected_mode_id", Doc<"Decoded mode ID">> detected_mode_id = 0U;
    Annotated<uint16_t, "packed_preamble", Doc<"Packed 12-bit preamble field">> packed_preamble = 0U;
    Annotated<std::size_t, "sync_start", Doc<"Sync start sample index">> sync_start = 0U;
    Annotated<std::size_t, "preamble_start", Doc<"Preamble start sample index">> preamble_start = 0U;

    GR_MAKE_REFLECTABLE(
        Cpfsk4PreambleDetect,
        in,
        detect_strobe,
        mode_id,
        profile,
        valid,
        detected_mode_id,
        packed_preamble,
        sync_start,
        preamble_start);

    std::vector<std::complex<float>> _buffer;
    bool                             _done         = false;
    bool                             _emit_strobe  = false;

    [[nodiscard]] cpfsk4_profile active_profile() const
    {
        if (mode_id != 0U) {
            if (auto resolved = cpfsk4_profile_for_mode_id(mode_id)) {
                return *resolved;
            }
            throw gr::exception(std::format("Cpfsk4PreambleDetect: no CPFSK profile for mode_id {}", mode_id));
        }
        if (auto resolved = cpfsk4_profile_by_name(profile)) {
            return *resolved;
        }
        throw gr::exception(std::format("Cpfsk4PreambleDetect: unknown profile '{}'", static_cast<std::string>(profile)));
    }

    void try_detect()
    {
        if (_done || _buffer.size() < 96000U) {
            return;
        }

        const auto params = active_profile();
        const auto result = detect_cpfsk4_preamble(
            _buffer,
            params.sync.bits,
            params.deviation_low_hz,
            params.deviation_high_hz,
            params.sample_rate_hz);

        valid            = result.valid;
        sync_start       = result.sync_start;
        preamble_start   = result.preamble_start;
        detected_mode_id = result.field.mode_id;
        if (result.valid) {
            packed_preamble = pack_preamble_field(result.field);
            _done           = true;
            _emit_strobe    = true;
        }
    }

    [[nodiscard]] work::Status processBulk(InputSpanLike auto& inputSpan, OutputSpanLike auto& outputSpan)
    {
        const std::size_t nIn = inputSpan.size();
        _buffer.insert(_buffer.end(), inputSpan.begin(), inputSpan.end());
        try_detect();

        const std::size_t nOut = outputSpan.size();
        std::size_t       published = 0U;
        for (std::size_t i = 0; i < nOut; ++i) {
            if (_emit_strobe) {
                outputSpan[published++] = static_cast<uint8_t>(1);
                _emit_strobe            = false;
            } else {
                outputSpan[published++] = static_cast<uint8_t>(0);
            }
        }
        outputSpan.publish(published);
        return published > 0U ? work::Status::OK : work::Status::INSUFFICIENT_OUTPUT_ITEMS;
    }
};

GR_REGISTER_BLOCK("gr::grident::PreambleDetectConsoleSink", gr::grident::PreambleDetectConsoleSink)

struct PreambleDetectConsoleSink : Block<PreambleDetectConsoleSink> {
    using Description = Doc<R""(@brief Print Cpfsk4PreambleDetect diagnostic fields when detect_strobe is set.)"">;

    PortIn<uint8_t> detect_strobe;

    Annotated<uint16_t, "expected_mode_id", Visible> expected_mode_id = 0U;
    Annotated<uint16_t, "detected_mode_id", Visible> detected_mode_id = 0U;
    Annotated<uint16_t, "packed_preamble", Visible>  packed_preamble = 0U;
    Annotated<bool, "valid", Visible>                valid = false;
    Annotated<std::size_t, "sync_start", Visible>    sync_start = 0U;

    GR_MAKE_REFLECTABLE(
        PreambleDetectConsoleSink,
        detect_strobe,
        expected_mode_id,
        detected_mode_id,
        packed_preamble,
        valid,
        sync_start);

    [[nodiscard]] work::Status processBulk(InputSpanLike auto& inputSpan)
    {
        for (const uint8_t sample : inputSpan) {
            if (sample == 0U) {
                continue;
            }
            std::printf(
                "gr-ident detect: valid=%s mode_id=%u packed=0x%04x sync_start=%zu\n",
                valid ? "true" : "false",
                static_cast<unsigned>(detected_mode_id),
                static_cast<unsigned>(packed_preamble),
                static_cast<std::size_t>(sync_start));
            if (expected_mode_id != 0U && detected_mode_id != expected_mode_id) {
                throw gr::exception(std::format(
                    "PreambleDetectConsoleSink: expected mode_id {} got {}",
                    expected_mode_id,
                    detected_mode_id));
            }
        }
        return work::Status::OK;
    }
};

static_assert(BlockLike<IqCf32FileSource>);
static_assert(BlockLike<Cpfsk4SyncCorrelator>);
static_assert(BlockLike<Cpfsk4PreambleDetect>);
static_assert(BlockLike<PreambleDetectConsoleSink>);

} // namespace gr::grident

#endif
