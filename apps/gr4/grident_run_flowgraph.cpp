#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/Graph_yaml_importer.hpp>
#include <gnuradio-4.0/GrIdentBlocks.hpp>
#include <gnuradio-4.0/GrTestingBlocks.hpp>
#include <gnuradio-4.0/Scheduler.hpp>
#include <gnuradio-4.0/SchedulerModel.hpp>
#include <gnuradio-4.0/grident/GrIdentIqBlocks.hpp>
#include <gnuradio-4.0/testing/NullSources.hpp>

#include <cstdlib>
#include <fstream>
#include <print>
#include <sstream>
#include <stdexcept>
#include <string>

#ifdef GRIDENT_HAS_ZMQ
#include <gnuradio-4.0/GrIdentZmqBlocks.hpp>
#endif

namespace {

std::string read_file(const std::string& path)
{
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("cannot open " + path);
    }
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return buffer.str();
}

std::string replace_all(std::string text, std::string_view needle, std::string_view value)
{
    std::size_t pos = 0;
    while ((pos = text.find(needle, pos)) != std::string::npos) {
        text.replace(pos, needle.size(), value);
        pos += value.size();
    }
    return text;
}

gr::PluginLoader make_loader()
{
    gr::BlockRegistry     block_registry;
    gr::SchedulerRegistry scheduler_registry;
    if (gr::blocklib::initGrIdentBlocks(block_registry) != 0) {
        throw std::runtime_error("initGrIdentBlocks failed");
    }
    if (gr::blocklib::initGrTestingBlocks(block_registry) != 0) {
        throw std::runtime_error("initGrTestingBlocks failed");
    }
#ifdef GRIDENT_HAS_ZMQ
    if (gr::blocklib::initGrIdentZmqBlocks(block_registry) != 0) {
        throw std::runtime_error("initGrIdentZmqBlocks failed");
    }
#endif
    return gr::PluginLoader(block_registry, scheduler_registry, {});
}

} // namespace

int main(int argc, char** argv)
{
    if (argc < 2) {
        std::println(stderr, "Usage: {} <flowgraph.gr.yaml> [key=value ...]", argv[0]);
        return EXIT_FAILURE;
    }

    try {
        std::string yaml = read_file(argv[1]);
        for (int i = 2; i < argc; ++i) {
            const std::string arg = argv[i];
            const auto        eq  = arg.find('=');
            if (eq == std::string::npos) {
                std::println(stderr, "Expected key=value, got {}", arg);
                return EXIT_FAILURE;
            }
            yaml = replace_all(yaml, arg.substr(0, eq), arg.substr(eq + 1));
        }

        auto                  loader = make_loader();
        auto                  loaded = gr::loadGrc(loader, yaml);
        auto                  scheduler = std::make_shared<gr::SchedulerWrapper<gr::scheduler::Simple<>>>();
        scheduler->setGraph(std::move(*loaded));
        scheduler->start();
        scheduler->stop();
        std::println("Flowgraph finished: {}", argv[1]);
        return EXIT_SUCCESS;
    } catch (const std::exception& ex) {
        std::println(stderr, "Flowgraph error: {}", ex.what());
        return EXIT_FAILURE;
    }
}
