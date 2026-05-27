project('grident', 'cpp',
        version : '0.1.0',
        default_options : ['cpp_std=c++17', 'warning_level=2'])

inc = include_directories('blocklib/grident/include')

subdir('blocklib/grident/lib')
subdir('blocklib/grident/test')

if get_option('gr4')
  subdir('blocklib/grident/blocks')
endif
