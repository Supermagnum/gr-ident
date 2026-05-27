#include <gnuradio-4.0/grident/GrIdentBlocks.hpp>
#include <gnuradio-4.0/grident/zeromq/ZmqTxControlSub.hpp>

#include <gnuradio/grident/preamble_codec.h>
#include <gnuradio/grident/preamble_field.h>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <print>
#include <string>
#include <thread>

#include <zmq.hpp>

namespace {

constexpr const char* k_endpoint = "tcp://127.0.0.1:5562";

void publish_grident_ptt(bool keyed)
{
    zmq::context_t ctx{ 1 };
    zmq::socket_t  pub{ ctx, zmq::socket_type::pub };
    pub.connect(k_endpoint);
    std::this_thread::sleep_for(std::chrono::milliseconds{ 100 });

    const char* topic   = "grident.tx";
    const char* payload = keyed ? "PTT_ON" : "PTT_OFF";
    pub.send(zmq::message_t(topic, std::strlen(topic)), zmq::send_flags::sndmore);
    pub.send(zmq::message_t(payload, std::strlen(payload)), zmq::send_flags::dontwait);
    std::this_thread::sleep_for(std::chrono::milliseconds{ 50 });
}

void publish_linht_ptt(bool keyed)
{
    zmq::context_t ctx{ 1 };
    zmq::socket_t  pub{ ctx, zmq::socket_type::pub };
    pub.connect(k_endpoint);
    std::this_thread::sleep_for(std::chrono::milliseconds{ 100 });

    const char* symbol = keyed ? "SOT" : "EOT";
    const auto  sym_len = static_cast<std::size_t>(std::strlen(symbol));
    unsigned char frame[6];
    frame[0] = 0x02U;
    frame[1] = static_cast<unsigned char>((sym_len >> 8) & 0xFFU);
    frame[2] = static_cast<unsigned char>(sym_len & 0xFFU);
    std::memcpy(frame + 3, symbol, sym_len);

    pub.send(zmq::message_t(frame, 3U + sym_len), zmq::send_flags::dontwait);
    std::this_thread::sleep_for(std::chrono::milliseconds{ 50 });
}

bool run_ptt_smoke(const char* profile, void (*publish)(bool))
{
    gr::grident::zeromq::ZmqTxControlSub tx;
    tx.profile     = profile;
    tx.endpoint    = k_endpoint;
    tx.bind        = true;
    tx.topic       = (std::string(profile) == "grident") ? "grident.tx" : "";
    tx.timeout_ms  = 10;
    tx.start();

    gr::grident::PreambleOnPtt ptt;
    ptt.mode_id   = 110U;
    ptt.digital   = true;
    ptt.encrypted = false;

    std::thread publisher([publish] {
        std::this_thread::sleep_for(std::chrono::milliseconds{ 150 });
        publish(true);
        std::this_thread::sleep_for(std::chrono::milliseconds{ 100 });
        publish(false);
    });

    const gr::grident::preamble_field expected_field{ 110U, false, true, false };
    const std::uint32_t               expected_codeword = gr::grident::encode_preamble(expected_field);

    bool saw_preamble = false;
    for (int i = 0; i < 600; ++i) {
        const std::uint8_t            tx_state = tx.processOne();
        const auto [codeword, tx_out]          = ptt.processOne(tx_state);
        if (codeword != 0U) {
            std::println("PTT/ZMQ smoke profile={} codeword=0x{:06x} tx_out={}", profile, codeword, tx_out);
            if (codeword == expected_codeword) {
                saw_preamble = true;
            }
        }
    }

    publisher.join();
    return saw_preamble;
}

} // namespace

int main()
{
    if (!run_ptt_smoke("grident", publish_grident_ptt)) {
        std::println(stderr, "PTT/ZMQ grident profile smoke test failed");
        return EXIT_FAILURE;
    }

    if (!run_ptt_smoke("linht", publish_linht_ptt)) {
        std::println(stderr, "PTT/ZMQ linht profile smoke test failed");
        return EXIT_FAILURE;
    }

    std::println("PTT/ZMQ smoke test OK");
    return EXIT_SUCCESS;
}
