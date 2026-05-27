#pragma once

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/annotated.hpp>
#include <gnuradio-4.0/meta/reflection.hpp>

#include <gnuradio-4.0/grident/zeromq/trait_helpers.hpp>

#include <cstring>
#include <string>
#include <vector>

#include <zmq.hpp>

namespace gr::grident::zeromq {

template<typename T>
concept ZmqPushSinkAcceptableTypes = VectorOfArithmeticOrComplex<T> || ArithmeticOrComplex<T>
    || std::is_same_v<T, std::string>;

template<typename T>
    requires ZmqPushSinkAcceptableTypes<T>
struct ZmqPushSink : Block<ZmqPushSink<T>> {
    using Description = Doc<R""(@brief PUSH stream samples or strings to a ZeroMQ endpoint.

Serializes arithmetic, complex, vector, or string samples as binary ZMQ messages.
Use with ZmqPullSource on a remote flowgraph for distributed IQ or data processing.)"">;

    PortIn<T> in;

    Annotated<std::string, "endpoint", Visible, Doc<"ZeroMQ endpoint (tcp://host:port)">> endpoint = "tcp://127.0.0.1:5555";
    Annotated<int, "timeout_ms", Visible, Doc<"Reserved for future send timeout handling">> timeout_ms = 100;
    Annotated<bool, "bind", Visible, Doc<"true = bind socket; false = connect">> bind = true;

    zmq::context_t _context{ 1 };
    zmq::socket_t  _socket{ _context, zmq::socket_type::push };

    GR_MAKE_REFLECTABLE(ZmqPushSink, in, endpoint, timeout_ms, bind);

    void start()
    {
        if (bind) {
            _socket.bind(endpoint);
        } else {
            _socket.connect(endpoint);
        }
    }

    [[nodiscard]] work::Status processBulk(InputSpanLike auto& inData)
    {
        if constexpr (VectorOfArithmeticOrComplex<T>) {
            for (auto& item : inData) {
                const std::size_t size_in_bytes = item.size() * sizeof(typename T::value_type);
                zmq::message_t    zmsg(size_in_bytes);
                std::memcpy(zmsg.data(), item.data(), size_in_bytes);
                _socket.send(zmsg, zmq::send_flags::none);
            }
        } else if constexpr (ArithmeticOrComplex<T>) {
            const std::size_t size_in_bytes = inData.size() * sizeof(T);
            zmq::message_t    zmsg(size_in_bytes);
            std::memcpy(zmsg.data(), inData.data(), size_in_bytes);
            _socket.send(zmsg, zmq::send_flags::none);
        } else if constexpr (std::is_same_v<T, std::string>) {
            for (const auto& text : inData) {
                zmq::message_t zmsg(text.size());
                if (!text.empty()) {
                    std::memcpy(zmsg.data(), text.data(), text.size());
                }
                _socket.send(zmsg, zmq::send_flags::none);
            }
        }

        return work::Status::OK;
    }
};

} // namespace gr::grident::zeromq

GR_REGISTER_BLOCK("gr::grident::zeromq::ZmqPushSink", gr::grident::zeromq::ZmqPushSink, ([T]), [ float, std::complex<float>, std::string, uint8_t, int32_t, std::vector<float>, std::vector<std::complex<float>> ])
