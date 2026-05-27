#ifndef GNURADIO_GRIDENT_BLOCKS_HPP
#define GNURADIO_GRIDENT_BLOCKS_HPP

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/annotated.hpp>
#include <gnuradio-4.0/meta/reflection.hpp>

#include <gnuradio/grident/golay24_12.h>
#include <gnuradio/grident/preamble_codec.h>
#include <gnuradio/grident/preamble_field.h>

namespace gr::grident {

GR_REGISTER_BLOCK("gr::grident::GolayEncode", gr::grident::GolayEncode)

struct GolayEncode : Block<GolayEncode> {
    using Description = Doc<R""(@brief Encode a 12-bit field with Golay(24,12).

Input: raw 12-bit value in the lower bits of a uint16 sample.
Output: 24-bit Golay codeword in uint32.)"">;

    PortIn<uint16_t>  in;
    PortOut<uint32_t> out;

    GR_MAKE_REFLECTABLE(GolayEncode, in, out);

    [[nodiscard]] constexpr uint32_t processOne(uint16_t raw) const noexcept
    {
        return golay24_12::encode(raw & 0x0fff);
    }
};

GR_REGISTER_BLOCK("gr::grident::GolayDecode", gr::grident::GolayDecode)

struct GolayDecode : Block<GolayDecode> {
    using Description = Doc<R""(@brief Decode a Golay(24,12) codeword to a 12-bit field.

Throws if the codeword is uncorrectable (>3 bit errors).)"">;

    PortIn<uint32_t>  in;
    PortOut<uint16_t> out;

    GR_MAKE_REFLECTABLE(GolayDecode, in, out);

    [[nodiscard]] uint16_t processOne(uint32_t codeword) const
    {
        const auto result = golay24_12::decode(codeword);
        if (!result.valid) {
            throw gr::exception("Golay(24,12) decode failed");
        }
        return result.data;
    }
};

GR_REGISTER_BLOCK("gr::grident::PreambleSource", gr::grident::PreambleSource)

struct PreambleSource : Block<PreambleSource> {
    using Description = Doc<R""(@brief Emit one gr-ident preamble Golay codeword.

Encodes mode_id, encrypted, and digital flags from block parameters.
Emits n_samples codewords (default 1) then stops.)"">;

    PortOut<uint32_t> out;

    Annotated<uint16_t, "mode_id", Visible, Doc<"Mode ID (0..511)">> mode_id = 120U;
    Annotated<bool, "encrypted", Visible, Doc<"Encrypted / open flag (bit 10)">> encrypted = false;
    Annotated<bool, "digital", Visible, Doc<"Analog / digital flag (bit 11)">> digital = true;
    Annotated<gr::Size_t, "n_samples", Doc<"Number of codewords to emit (0 = infinite)">> n_samples = 1U;
    Annotated<gr::Size_t, "count", Doc<"Emitted sample count (diagnostics)">> count = 0U;

    GR_MAKE_REFLECTABLE(PreambleSource, out, mode_id, encrypted, digital, n_samples, count);

    void reset() { count = 0U; }

    [[nodiscard]] uint32_t processOne()
    {
        count++;
        if (n_samples > 0 && count > n_samples) {
            this->requestStop();
        }

        preamble_field field{ mode_id, encrypted, digital };
        return encode_preamble(field);
    }
};

GR_REGISTER_BLOCK("gr::grident::PreambleDecode", gr::grident::PreambleDecodeBlock)

struct PreambleDecodeBlock : Block<PreambleDecodeBlock> {
    using Description = Doc<R""(@brief Decode a gr-ident preamble Golay codeword.

Output is the 12-bit packed preamble field (mode ID and flags).
Use unpack_preamble_field in downstream logic for structured access.)"">;

    PortIn<uint32_t>  in;
    PortOut<uint16_t> out;

    GR_MAKE_REFLECTABLE(PreambleDecodeBlock, in, out);

    [[nodiscard]] uint16_t processOne(uint32_t codeword) const
    {
        const auto status = decode_preamble(codeword);
        if (!status.golay.valid) {
            throw gr::exception("gr-ident preamble Golay decode failed");
        }
        return status.golay.data;
    }
};

static_assert(BlockLike<GolayEncode>);
static_assert(BlockLike<GolayDecode>);
static_assert(BlockLike<PreambleSource>);
static_assert(BlockLike<PreambleDecodeBlock>);

} // namespace gr::grident

#endif
