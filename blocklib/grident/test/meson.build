test_golay = executable(
    'test_golay',
    'test_golay.cc',
    dependencies : [grident_dep],
)

test_preamble_field = executable(
    'test_preamble_field',
    'test_preamble_field.cc',
    dependencies : [grident_dep],
)

test('golay codec', test_golay)
test('preamble field', test_preamble_field)

test_metadata_field = executable(
    'test_metadata_field',
    'test_metadata_field.cc',
    dependencies : [grident_dep],
)

test('metadata field', test_metadata_field)

test_tx_control = executable(
    'test_tx_control',
    'test_tx_control.cc',
    dependencies : [grident_dep],
)

test('tx control parse', test_tx_control)
