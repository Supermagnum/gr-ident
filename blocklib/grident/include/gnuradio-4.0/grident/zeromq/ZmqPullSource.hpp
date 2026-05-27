#pragma once

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/annotated.hpp>
#include <gnuradio-4.0/meta/reflection.hpp>

#include <gnuradio-4.0/grident/zeromq/trait_helpers.hpp>

#include <algorithm>
#include <chrono>
#include <cstring>
#include <string>
#include <vector>

#include <zmq.hpp>

namespace gr::grident::zeromq {

template<typename T>
concept ZmqPullSourceAcceptableTypes = VectorOfArithmeticOrComplex<T> || ArithmeticOrComplex<T>
    || std::is_same_v<T, std::string>;

template<typename T>
    requires ZmqPullSourceAcceptableTypes<T>
struct ZmqPullSource : Block<ZmqPullSource<T>> {
    using Description = Doc<R""(@brief PULL stream samples or strings from a ZeroMQ endpoint.

Receives binary ZMQ messages produced by ZmqPushSink. Supports distributed IQ capture
and inter-process flowgraph edges.)"">;

    PortOut<T> out;

    Annotated<std::string, "endpoint", Visible, Doc<"ZeroMQ endpoint (tcp://host:port)">> endpoint = "tcp://127.0.0.1:5555";
    Annotated<int, "timeout_ms", Visible, Doc<"Poll timeout in milliseconds">> timeout_ms = 100;
    Annotated<bool, "bind", Visible, Doc<"true = bind socket; false = connect">> bind = false;

    zmq::context_t      _context{ 1 };
    zmq::socket_t       _socket{ _context, zmq::socket_type::pull };
    std::vector<T>      _pending_items;

    GR_MAKE_REFLECTABLE(ZmqPullSource, out, endpoint, timeout_ms, bind);

    void start()
    {
        if (bind) {
            _socket.bind(endpoint);
        } else {
            _socket.connect(endpoint);
        }
    }

    [[nodiscard]] work::Status processBulk(OutputSpanLike auto& outputSpan) noexcept
    {
        const std::size_t nProcessOut = outputSpan.size();
        std::size_t         npublished = 0;

        if constexpr (VectorOfArithmeticOrComplex<T>) {
            for (std::size_t i = 0; i < nProcessOut; ++i) {
                zmq::pollitem_t items[] = { { static_cast<void*>(_socket), 0, ZMQ_POLLIN, 0 } };
                zmq::poll(items, 1, std::chrono::milliseconds{ timeout_ms });

                if (items[0].revents & ZMQ_POLLIN) {
                    zmq::message_t msg;
                    static_cast<void>(_socket.recv(msg));
                    auto& vec = outputSpan[i];
                    const std::size_t nels = msg.size() / sizeof(typename T::value_type);
                    vec.resize(nels);
                    std::memcpy(vec.data(), msg.data(), msg.size());
                    ++npublished;
                } else {
                    break;
                }
            }
        } else if constexpr (ArithmeticOrComplex<T>) {
            while (true) {
                std::size_t room_in_span = nProcessOut - npublished;
                if (!_pending_items.empty()) {
                    const auto n = std::min(room_in_span, _pending_items.size());
                    std::copy(_pending_items.begin(), _pending_items.begin() + static_cast<std::ptrdiff_t>(n),
                        outputSpan.begin() + static_cast<std::ptrdiff_t>(npublished));
                    npublished += n;
                    _pending_items.erase(_pending_items.begin(),
                        _pending_items.begin() + static_cast<std::ptrdiff_t>(n));
                }

                room_in_span = nProcessOut - npublished;
                if (room_in_span == 0) {
                    break;
                }

                zmq::pollitem_t items[] = { { static_cast<void*>(_socket), 0, ZMQ_POLLIN, 0 } };
                zmq::poll(items, 1, std::chrono::milliseconds{ timeout_ms });

                if (items[0].revents & ZMQ_POLLIN) {
                    zmq::message_t msg;
                    static_cast<void>(_socket.recv(msg));
                    const std::size_t nels = msg.size() / sizeof(T);
                    const std::size_t n = std::min(nels, room_in_span);
                    const std::size_t rem = nels - n;
                    std::memcpy(outputSpan.data() + npublished, msg.data(), n * sizeof(T));
                    npublished += n;
                    if (rem > 0) {
                        const auto prev = _pending_items.size();
                        _pending_items.resize(prev + rem);
                        std::memcpy(_pending_items.data() + prev,
                            static_cast<const T*>(msg.data()) + n,
                            rem * sizeof(T));
                    }
                    break;
                }
                break;
            }
        } else if constexpr (std::is_same_v<T, std::string>) {
            for (std::size_t i = 0; i < nProcessOut; ++i) {
                zmq::pollitem_t items[] = { { static_cast<void*>(_socket), 0, ZMQ_POLLIN, 0 } };
                zmq::poll(items, 1, std::chrono::milliseconds{ timeout_ms });

                if (items[0].revents & ZMQ_POLLIN) {
                    zmq::message_t msg;
                    static_cast<void>(_socket.recv(msg));
                    outputSpan[i] = std::string(static_cast<const char*>(msg.data()), msg.size());
                    ++npublished;
                } else {
                    break;
                }
            }
        }

        outputSpan.publish(npublished);
        return work::Status::OK;
    }
};

} // namespace gr::grident::zeromq

GR_REGISTER_BLOCK("gr::grident::zeromq::ZmqPullSource", gr::grident::zeromq::ZmqPullSource, ([T]), [ float, std::complex<float>, std::string, uint8_t, int32_t, std::vector<float>, std::vector<std::complex<float>> ])
