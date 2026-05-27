cmake_minimum_required(VERSION 3.24)

if(NOT DEFINED CMAKE_CXX_COMPILER)
    find_program(GXX14 NAMES g++-14)
    if(GXX14)
        set(CMAKE_CXX_COMPILER "${GXX14}" CACHE FILEPATH "GNU Radio 4 requires C++23" FORCE)
    endif()
endif()

project(grident LANGUAGES CXX VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(NOT CMAKE_PREFIX_PATH)
    list(APPEND CMAKE_PREFIX_PATH "/opt/gnuradio4-gcc")
endif()

find_package(gnuradio4 REQUIRED CONFIG)

set(GNURADIO_BLOCKLIB_MACROS "/opt/gnuradio4-gcc/lib/GnuRadioBlockLib/GnuRadioBlockLibMacros.cmake")
if(NOT EXISTS "${GNURADIO_BLOCKLIB_MACROS}")
    message(FATAL_ERROR "GnuRadioBlockLibMacros.cmake not found at ${GNURADIO_BLOCKLIB_MACROS}")
endif()
include("${GNURADIO_BLOCKLIB_MACROS}")
set(PARSER_EXECUTABLE "/opt/gnuradio4-gcc/bin/gnuradio_4_0_parse_registrations")

set(GRIDENT_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/blocklib/grident/include")

set(GRIDENT_CODEC_SOURCES
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/golay24_12.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/preamble_field.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/preamble_codec.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/metadata_field.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/tx_control.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/mode_table.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/sync_correlator.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/sync_sequences_data.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/modulation_profile.cc"
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/preamble_detect.cc"
)

gr_add_block_library(GrIdentBlocks
    HEADERS
        "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/GrIdentBlocks.hpp"
        "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/GrIdentIqBlocks.hpp"
    SOURCES ${GRIDENT_CODEC_SOURCES}
    MAKE_SHARED_LIBRARY
    SPLIT_BLOCK_INSTANTIATIONS
)

target_include_directories(GrIdentBlocksObject PUBLIC "${GRIDENT_INCLUDE_DIR}")

find_package(PkgConfig)
if(PkgConfig_FOUND)
    pkg_check_modules(GRIDENT_ZMQ QUIET libzmq)
endif()

if(GRIDENT_ZMQ_FOUND)
    message(STATUS "gr-ident: building ZeroMQ GR4 blocks (libzmq ${GRIDENT_ZMQ_VERSION})")

    set(GRIDENT_ZMQ_BLOCK_HEADERS
        "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/zeromq/ZmqPushSink.hpp"
        "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/zeromq/ZmqPullSource.hpp"
        "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/zeromq/PreambleResultZmqPub.hpp"
        "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/zeromq/ZmqTxControlSub.hpp"
    )

    gr_add_block_library(GrIdentZmqBlocks
        HEADERS ${GRIDENT_ZMQ_BLOCK_HEADERS}
        SOURCES ${GRIDENT_CODEC_SOURCES}
        MAKE_SHARED_LIBRARY
        SPLIT_BLOCK_INSTANTIATIONS
    )

    target_include_directories(GrIdentZmqBlocksObject PUBLIC "${GRIDENT_INCLUDE_DIR}")
    target_include_directories(GrIdentZmqBlocksObject PUBLIC ${GRIDENT_ZMQ_INCLUDE_DIRS})
    target_link_libraries(GrIdentZmqBlocksObject PUBLIC ${GRIDENT_ZMQ_LIBRARIES})
    target_compile_definitions(GrIdentZmqBlocksObject PUBLIC GRIDENT_HAS_ZMQ=1)
else()
    message(STATUS "gr-ident: ZeroMQ blocks disabled (install libzmq3-dev / cppzmq)")
endif()

enable_testing()

set(GRIDENT_GR4_APP_INCLUDES
    "${CMAKE_BINARY_DIR}/include"
    "${GRIDENT_INCLUDE_DIR}"
)

function(grident_add_gr4_app target)
    target_include_directories(${target} PRIVATE ${GRIDENT_GR4_APP_INCLUDES})
    target_link_libraries(${target} PRIVATE
        gnuradio4::gnuradio-core
        gnuradio4::gnuradio-blocklib-core
        gnuradio4::GrTestingBlocksShared
        GrIdentBlocksShared
    )
endfunction()

add_executable(grident_receive_flowgraph apps/gr4/grident_receive_flowgraph.cpp)
target_link_libraries(grident_receive_flowgraph PRIVATE GrIdentBlocksShared)
target_include_directories(grident_receive_flowgraph PRIVATE ${GRIDENT_GR4_APP_INCLUDES})

add_executable(grident_run_flowgraph apps/gr4/grident_run_flowgraph.cpp)
grident_add_gr4_app(grident_run_flowgraph)
if(GRIDENT_ZMQ_FOUND)
    target_compile_definitions(grident_run_flowgraph PRIVATE GRIDENT_HAS_ZMQ=1)
    target_link_libraries(grident_run_flowgraph PRIVATE GrIdentZmqBlocksShared ${GRIDENT_ZMQ_LIBRARIES})
    target_include_directories(grident_run_flowgraph PRIVATE ${GRIDENT_ZMQ_INCLUDE_DIRS})
endif()

if(GRIDENT_ZMQ_FOUND)
    add_executable(grident_ptt_zmq_smoke apps/gr4/grident_ptt_zmq_smoke.cpp)
    grident_add_gr4_app(grident_ptt_zmq_smoke)
    target_link_libraries(grident_ptt_zmq_smoke PRIVATE GrIdentZmqBlocksShared ${GRIDENT_ZMQ_LIBRARIES})
    target_include_directories(grident_ptt_zmq_smoke PRIVATE ${GRIDENT_ZMQ_INCLUDE_DIRS})
endif()

add_executable(grident_registry_test blocklib/grident/test/test_registry.cc)
target_link_libraries(grident_registry_test PRIVATE gnuradio4::gnuradio-core gnuradio4::gnuradio-blocklib-core)
target_include_directories(grident_registry_test PRIVATE "${CMAKE_BINARY_DIR}/include" "${GRIDENT_INCLUDE_DIR}")

add_dependencies(grident_registry_test GrIdentBlocksShared)
target_link_libraries(grident_registry_test PRIVATE GrIdentBlocksShared)

add_test(NAME grident_registry COMMAND grident_registry_test)

add_test(
    NAME grident_receive_flowgraph
    COMMAND grident_receive_flowgraph
        "${CMAKE_SOURCE_DIR}/python/tests/fixtures/common_modes/mode_110.cf32"
        110
)

if(GRIDENT_ZMQ_FOUND)
    add_test(NAME grident_ptt_zmq_smoke COMMAND grident_ptt_zmq_smoke)
endif()
