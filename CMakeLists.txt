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
    "${CMAKE_SOURCE_DIR}/blocklib/grident/lib/mode_table.cc"
)

gr_add_block_library(GrIdentBlocks
    HEADERS "${GRIDENT_INCLUDE_DIR}/gnuradio-4.0/grident/GrIdentBlocks.hpp"
    SOURCES ${GRIDENT_CODEC_SOURCES}
    MAKE_SHARED_LIBRARY
    SPLIT_BLOCK_INSTANTIATIONS
)

target_include_directories(GrIdentBlocksObject PUBLIC "${GRIDENT_INCLUDE_DIR}")

enable_testing()

add_executable(grident_registry_test blocklib/grident/test/test_registry.cc)
target_link_libraries(grident_registry_test PRIVATE gnuradio4::gnuradio-core gnuradio4::gnuradio-blocklib-core)
target_include_directories(grident_registry_test PRIVATE "${CMAKE_BINARY_DIR}/include" "${GRIDENT_INCLUDE_DIR}")

add_dependencies(grident_registry_test GrIdentBlocksShared)
target_link_libraries(grident_registry_test PRIVATE GrIdentBlocksShared)

add_test(NAME grident_registry COMMAND grident_registry_test)
