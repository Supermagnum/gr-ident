#include <gnuradio/grident/modulation_profile.h>

#include <array>

namespace gr {
namespace grident {
namespace {

constexpr float k_dev_etsi_nb_low  = 648.0F;
constexpr float k_dev_etsi_nb_high = 1944.0F;
constexpr int   k_sample_rate      = 48000;

constexpr cpfsk4_profile k_nfm_125_4800 = {
    "nfm_125_4800",
    { "sync_nfm", {} },
    k_dev_etsi_nb_low,
    k_dev_etsi_nb_high,
    k_sample_rate,
    true,
};


constexpr cpfsk4_profile k_nfm_ctcss = [] {
    auto p = k_nfm_125_4800;
    p.name = "nfm_125_ctcss_4800";
    return p;
}();

constexpr cpfsk4_profile k_nfm_dcs = [] {
    auto p = k_nfm_125_4800;
    p.name = "nfm_125_dcs_4800";
    return p;
}();

constexpr cpfsk4_profile k_c4fm = [] {
    auto p = k_nfm_125_4800;
    p.name = "c4fm_4800";
    return p;
}();

constexpr cpfsk4_profile k_dpmr = [] {
    auto p = k_nfm_125_4800;
    p.name = "dpmr_4800";
    return p;
}();

constexpr cpfsk4_profile k_dmr = [] {
    auto p = k_nfm_125_4800;
    p.name = "dmr_4800";
    return p;
}();

constexpr cpfsk4_profile k_nxdn = [] {
    auto p = k_nfm_125_4800;
    p.name = "nxdn_4800";
    return p;
}();

constexpr cpfsk4_profile k_m17 = [] {
    auto p = k_nfm_125_4800;
    p.name = "m17_4800";
    return p;
}();

constexpr cpfsk4_profile k_dstar = [] {
    auto p = k_nfm_125_4800;
    p.name = "dstar_4800";
    return p;
}();

struct mode_profile_entry {
    std::uint16_t    mode_id;
    cpfsk4_profile   profile;
    std::string_view sync_name;
};

// Sync names resolved at lookup time so constexpr arrays stay simple.
constexpr mode_profile_entry k_mode_profiles[] = {
    { 20, k_nfm_125_4800, "sync_nfm" },
    { 21, k_nfm_125_4800, "sync_nfm" },
    { 22, k_nfm_125_4800, "sync_nfm" },
    { 30, k_nfm_ctcss, "sync_nfm" },
    { 40, k_nfm_dcs, "sync_nfm" },
    { 104, k_c4fm, "sync_c4fm" },
    { 108, k_dpmr, "sync_dpmr" },
    { 110, k_nfm_125_4800, "sync_nfm" },
    { 100, k_dmr, "sync_dmr" },
    { 103, k_dstar, "sync_dstar" },
    { 107, k_nxdn, "sync_nxdn" },
    { 120, k_m17, "sync_m17" },
};

cpfsk4_profile resolve_profile(cpfsk4_profile profile, std::string_view sync_name)
{
    profile.sync = sync_sequence_by_name(sync_name);
    return profile;
}

} // namespace

std::optional<cpfsk4_profile> cpfsk4_profile_by_name(std::string_view name)
{
    if (name == "nfm_125_4800") {
        return resolve_profile(k_nfm_125_4800, "sync_nfm");
    }
    if (name == "nfm_125_ctcss_4800") {
        return resolve_profile(k_nfm_ctcss, "sync_nfm");
    }
    if (name == "nfm_125_dcs_4800") {
        return resolve_profile(k_nfm_dcs, "sync_nfm");
    }
    if (name == "c4fm_4800") {
        return resolve_profile(k_c4fm, "sync_c4fm");
    }
    if (name == "dpmr_4800") {
        return resolve_profile(k_dpmr, "sync_dpmr");
    }
    if (name == "dmr_4800") {
        return resolve_profile(k_dmr, "sync_dmr");
    }
    if (name == "nxdn_4800") {
        return resolve_profile(k_nxdn, "sync_nxdn");
    }
    if (name == "m17_4800") {
        return resolve_profile(k_m17, "sync_m17");
    }
    if (name == "dstar_4800") {
        return resolve_profile(k_dstar, "sync_dstar");
    }
    return std::nullopt;
}

std::optional<cpfsk4_profile> cpfsk4_profile_for_mode_id(std::uint16_t mode_id)
{
    for (const auto& entry : k_mode_profiles) {
        if (entry.mode_id == mode_id) {
            return resolve_profile(entry.profile, entry.sync_name);
        }
    }
    return std::nullopt;
}

} // namespace grident
} // namespace gr
