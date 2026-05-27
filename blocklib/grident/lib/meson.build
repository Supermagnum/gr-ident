grident_lib_sources = files(
    'golay24_12.cc',
    'preamble_field.cc',
    'preamble_codec.cc',
    'metadata_field.cc',
    'tx_control.cc',
    'mode_table.cc',
    'sync_correlator.cc',
    'sync_sequences_data.cc',
    'modulation_profile.cc',
    'preamble_detect.cc',
)

grident_lib = static_library(
    'grident',
    grident_lib_sources,
    include_directories : inc,
    install : false,
)

grident_dep = declare_dependency(
    include_directories : inc,
    link_with : grident_lib,
)

meson.override_dependency('grident', grident_dep)
