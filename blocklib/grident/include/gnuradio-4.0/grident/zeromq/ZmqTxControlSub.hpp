#pragma once

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/annotated.hpp>
#include <gnuradio-4.0/meta/reflection.hpp>

#include <gnuradio/grident/tx_control.h>

#include <chrono>
#include <cstring>
#include <string>

#include <zmq.hpp>

namespace gr::grident::zeromq {

struct ZmqTxControlSub : Block<ZmqTxControlSub> {
    using Description = Doc<R""(@brief Subscribe to ZeroMQ TX/PTT control messages.

Outputs a uint8 stream: 1 while PTT/TX is active, 0 while idle. Wire to PreambleOnPtt
to insert the gr-ident preamble burst on key-down.

LinHT profile (default): single-part GNU Radio PMT strings on ipc:///tmp/ptt_msg
  SOT (start of transmit), EOT (end of transmit) -- wire format 0x02, uint16 BE len, payload.

grident profile: multipart [topic, body] with topic grident.tx and JSON or plain text:
  PTT_ON, PTT_OFF, TX, RX, KEYDOWN, KEYUP, 1, 0
  {"ptt": true}, {"ptt": false}, {"tx": 1}, {"tx": 0})"">;

    PortOut<uint8_t> tx_state;

    Annotated<std::string, "profile", Visible,
        Doc<"linht (LinHT PMT SOT/EOT) or grident (multipart JSON/text on grident.tx)">> profile = "linht";
    Annotated<std::string, "endpoint", Visible, Doc<"ZeroMQ SUB endpoint">> endpoint = linht_ptt_endpoint;
    Annotated<bool, "bind", Visible, Doc<"true = bind SUB socket; false = connect">> bind = false;
    Annotated<std::string, "topic", Visible, Doc<"SUB topic filter (empty = all messages)">> topic = "";
    Annotated<int, "timeout_ms", Visible, Doc<"Poll timeout in milliseconds">> timeout_ms = 50;

    zmq::context_t _context{ 1 };
    zmq::socket_t  _socket{ _context, zmq::socket_type::sub };

    GR_MAKE_REFLECTABLE(ZmqTxControlSub, tx_state, profile, endpoint, bind, topic, timeout_ms);

    bool _tx_active = false;

    void start()
    {
        const std::string ep = endpoint;
        if (bind) {
            _socket.bind(ep);
        } else {
            _socket.connect(ep);
        }
        const std::string filter = topic;
        _socket.set(zmq::sockopt::subscribe, filter);
    }

    void poll_control()
    {
        zmq::pollitem_t items[] = { { static_cast<void*>(_socket), 0, ZMQ_POLLIN, 0 } };
        zmq::poll(items, 1, std::chrono::milliseconds{ timeout_ms });

        while (items[0].revents & ZMQ_POLLIN) {
            zmq::message_t msg;
            if (!_socket.recv(msg, zmq::recv_flags::dontwait)) {
                break;
            }

            const char* payload = static_cast<const char*>(msg.data());
            std::size_t length  = msg.size();
            if (msg.more()) {
                zmq::message_t body;
                if (auto got = _socket.recv(body, zmq::recv_flags::none); got) {
                    payload = static_cast<const char*>(body.data());
                    length  = body.size();
                }
            }

            const auto state = parse_tx_control_message(payload, length);
            if (state == tx_control_state::on) {
                _tx_active = true;
            } else if (state == tx_control_state::off) {
                _tx_active = false;
            }
        }
    }

    [[nodiscard]] uint8_t processOne()
    {
        poll_control();
        return _tx_active ? static_cast<uint8_t>(1) : static_cast<uint8_t>(0);
    }
};

static_assert(BlockLike<ZmqTxControlSub>);

} // namespace gr::grident::zeromq

GR_REGISTER_BLOCK("gr::grident::zeromq::ZmqTxControlSub", gr::grident::zeromq::ZmqTxControlSub)
