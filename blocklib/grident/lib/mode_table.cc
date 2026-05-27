#include <gnuradio/grident/mode_table.h>

namespace gr {
namespace grident {

namespace {

struct mode_entry {
    uint16_t id;
    mode_info info;
};

constexpr mode_entry k_modes[] = {
    { 0, { "Null / unassigned", false, "reserved" } },
    { 511, { "Test / loopback", true, "reserved" } },
    { 1, { "AM", false, "analog" } },
    { 2, { "AM-DSB", false, "analog" } },
    { 3, { "AM-SSB", false, "analog" } },
    { 4, { "USB", false, "analog" } },
    { 5, { "LSB", false, "analog" } },
    { 6, { "DSB-SC", false, "analog" } },
    { 10, { "WFM", false, "analog" } },
    { 11, { "WFM Stereo", false, "analog" } },
    { 12, { "FM 25 kHz", false, "analog" } },
    { 13, { "FM 20 kHz", false, "analog" } },
    { 20, { "NFM 12.5 kHz", false, "analog" } },
    { 21, { "NFM 8.33 kHz", false, "analog" } },
    { 22, { "NFM 6.25 kHz", false, "analog" } },
    { 30, { "NFM 12.5 kHz + CTCSS", false, "analog" } },
    { 31, { "NFM 8.33 kHz + CTCSS", false, "analog" } },
    { 32, { "NFM 6.25 kHz + CTCSS", false, "analog" } },
    { 33, { "FM 25 kHz + CTCSS", false, "analog" } },
    { 34, { "FM 20 kHz + CTCSS", false, "analog" } },
    { 40, { "NFM 12.5 kHz + DCS", false, "analog" } },
    { 41, { "NFM 8.33 kHz + DCS", false, "analog" } },
    { 42, { "NFM 6.25 kHz + DCS", false, "analog" } },
    { 43, { "FM 25 kHz + DCS", false, "analog" } },
    { 44, { "FM 20 kHz + DCS", false, "analog" } },
    { 50, { "NFM 12.5 kHz + CTCSS + DCS", false, "analog" } },
    { 51, { "NFM 8.33 kHz + CTCSS + DCS", false, "analog" } },
    { 52, { "NFM 6.25 kHz + CTCSS + DCS", false, "analog" } },
    { 60, { "CW", false, "analog" } },
    { 61, { "CW Narrow", false, "analog" } },
    { 62, { "NBAM", false, "analog" } },
    { 63, { "ECSS", false, "analog" } },
    { 100, { "DMR", true, "digital" } },
    { 101, { "DMR Tier II", true, "digital" } },
    { 102, { "DMR Tier III", true, "digital" } },
    { 103, { "D-STAR", true, "digital" } },
    { 104, { "C4FM / Fusion", true, "digital" } },
    { 105, { "P25 Phase 1", true, "digital" } },
    { 106, { "P25 Phase 2", true, "digital" } },
    { 107, { "NXDN", true, "digital" } },
    { 108, { "dPMR", true, "digital" } },
    { 109, { "TETRA", true, "digital" } },
    { 110, { "EchoLink", true, "linking" } },
    { 111, { "IRLP", true, "linking" } },
    { 112, { "AllStar Link", true, "linking" } },
    { 113, { "Mumble", true, "linking" } },
    { 114, { "Wires-X", true, "linking" } },
    { 115, { "D-STAR Reflector", true, "linking" } },
    { 120, { "M17 Codec2 3200", true, "digital" } },
    { 121, { "M17 Codec2 1600", true, "digital" } },
    { 122, { "FreeDV 700D", true, "digital" } },
    { 123, { "FreeDV 1600", true, "digital" } },
    { 124, { "FreeDV 2020", true, "digital" } },
    { 125, { "Codec2 2400", true, "digital" } },
    { 126, { "Codec2 1200", true, "digital" } },
    { 127, { "Opus", true, "digital" } },
    { 150, { "AX.25", true, "data" } },
    { 151, { "APRS", true, "data" } },
    { 152, { "VARA HF", true, "data" } },
    { 153, { "VARA FM", true, "data" } },
    { 154, { "Winlink", true, "data" } },
    { 158, { "PSK31", true, "data" } },
    { 159, { "RTTY", true, "data" } },
    { 180, { "OFDM", true, "digital" } },
    { 181, { "COFDM", true, "digital" } },
    { 210, { "SSTV Martin M1", false, "image" } },
    { 211, { "SSTV Martin M2", false, "image" } },
    { 212, { "SSTV Scottie S1", false, "image" } },
    { 213, { "SSTV Scottie S2", false, "image" } },
    { 214, { "SSTV Scottie DX", false, "image" } },
    { 215, { "SSTV Robot 36", false, "image" } },
    { 216, { "SSTV Robot 72", false, "image" } },
    { 217, { "SSTV PD 90", false, "image" } },
    { 218, { "SSTV PD 120", false, "image" } },
    { 219, { "SSTV PD 160", false, "image" } },
    { 220, { "SSTV PD 180", false, "image" } },
    { 221, { "SSTV PD 240", false, "image" } },
    { 222, { "SSTV Wraase SC2-120", false, "image" } },
    { 223, { "SSTV Wraase SC2-180", false, "image" } },
    { 230, { "DSSTV", true, "image" } },
    { 231, { "EasyPal", true, "image" } },
    { 232, { "FSSTV", true, "image" } },
    { 233, { "FAX", true, "image" } },
    { 240, { "ATV", false, "image" } },
    { 241, { "ATV NTSC", false, "image" } },
    { 242, { "ATV PAL", false, "image" } },
    { 243, { "DATV DVB-S", true, "image" } },
    { 244, { "DATV DVB-S2", true, "image" } },
    { 245, { "DATV DVB-T", true, "image" } },
    { 260, { "Linear transponder", false, "satellite" } },
    { 261, { "FM Satellite", false, "satellite" } },
    { 262, { "FM Satellite + CTCSS", false, "satellite" } },
    { 264, { "QO-100 NB", false, "satellite" } },
    { 265, { "QO-100 WB", true, "satellite" } },
};

} // namespace

std::optional<mode_info> lookup_mode(uint16_t mode_id)
{
    for (const auto& entry : k_modes) {
        if (entry.id == mode_id) {
            return entry.info;
        }
    }
    return std::nullopt;
}

const char* mode_name(uint16_t mode_id)
{
    if (const auto info = lookup_mode(mode_id)) {
        return info->name.data();
    }
    return "unknown";
}

} // namespace grident
} // namespace gr
