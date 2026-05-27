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
