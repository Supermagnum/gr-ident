#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/GrIdentBlocks.hpp>
#include <gnuradio-4.0/grident/GrIdentIqBlocks.hpp>

#include <cstdio>
#include <cstdlib>
#include <string_view>

static bool has_block(const gr::BlockRegistry& registry, std::string_view name)
{
    for (const auto& key : registry.keys()) {
        if (key == name) {
            return true;
        }
    }
    return false;
}

int main()
{
    gr::BlockRegistry registry;
    const std::size_t failures = gr::blocklib::initGrIdentBlocks(registry);
    if (failures != 0) {
        std::fprintf(stderr, "Block registration reported %zu failure(s)\n", failures);
        return EXIT_FAILURE;
    }

    const char* blocks[] = {
        "gr::grident::GolayEncode",
        "gr::grident::GolayDecode",
        "gr::grident::PreambleSource",
        "gr::grident::PreambleOnPtt",
        "gr::grident::PreambleDecode",
        "gr::grident::IqCf32FileSource",
        "gr::grident::Cpfsk4SyncCorrelator",
        "gr::grident::Cpfsk4PreambleDetect",
    };

    for (const char* name : blocks) {
        if (!has_block(registry, name)) {
            std::fprintf(stderr, "Missing block: %s\n", name);
            return EXIT_FAILURE;
        }
    }

    gr::property_map params;
    auto block = registry.create("gr::grident::PreambleSource", params);
    if (!block) {
        std::fprintf(stderr, "Failed to instantiate PreambleSource\n");
        return EXIT_FAILURE;
    }

    std::printf("Registered %zu gr-ident block type(s)\n", sizeof(blocks) / sizeof(blocks[0]));
    return EXIT_SUCCESS;
}
