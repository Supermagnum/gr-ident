#pragma once

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/annotated.hpp>
#include <gnuradio-4.0/meta/reflection.hpp>

#include <gnuradio/grident/preamble_field.h>

#include <cstring>
#include <format>
#include <string>

#include <zmq.hpp>

namespace gr::grident::zeromq {

struct PreambleResultZmqPub : Block<PreambleResultZmqPub> {
    using Description = Doc<R""(@brief Publish decoded gr-ident preamble fields as JSON over ZeroMQ PUB.

Connect upstream to PreambleDecode output (packed uint16). Subscribers receive JSON objects
with mode_id, digital, encrypted, and metadata_present fields.)"">;

    PortIn<uint16_t>  in;
    PortOut<uint16_t> out;

    Annotated<std::string, "endpoint", Visible, Doc<"ZeroMQ PUB endpoint (tcp://host:port)">> endpoint =
        "tcp://127.0.0.1:5560";
    Annotated<bool, "bind", Visible, Doc<"true = bind PUB socket; false = connect">> bind = true;
    Annotated<std::string, "topic", Visible, Doc<"Optional topic prefix sent as first frame">> topic = "grident";

    zmq::context_t _context{ 1 };
    zmq::socket_t  _socket{ _context, zmq::socket_type::pub };

    GR_MAKE_REFLECTABLE(PreambleResultZmqPub, in, out, endpoint, bind, topic);

    void start()
    {
        if (bind) {
            _socket.bind(endpoint);
        } else {
            _socket.connect(endpoint);
        }
    }

    [[nodiscard]] uint16_t processOne(uint16_t packed)
    {
        const auto field = unpack_preamble_field(packed, false);
        const std::string payload = std::format(
            R"({{"mode_id":{},"digital":{},"encrypted":{},"metadata_present":{}}})",
            field.mode_id,
            field.digital ? "true" : "false",
            field.encrypted ? "true" : "false",
            field.metadata_present ? "true" : "false");

        if (!topic.empty()) {
            zmq::message_t topic_frame(topic.size());
            if (!topic.empty()) {
                std::memcpy(topic_frame.data(), topic.data(), topic.size());
            }
            _socket.send(topic_frame, zmq::send_flags::sndmore);
        }

        zmq::message_t body(payload.size());
        if (!payload.empty()) {
            std::memcpy(body.data(), payload.data(), payload.size());
        }
        _socket.send(body, zmq::send_flags::dontwait);
        return packed;
    }
};

static_assert(BlockLike<PreambleResultZmqPub>);

} // namespace gr::grident::zeromq

GR_REGISTER_BLOCK("gr::grident::zeromq::PreambleResultZmqPub", gr::grident::zeromq::PreambleResultZmqPub)
