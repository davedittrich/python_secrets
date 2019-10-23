load test_helper

# See definition of PSEC in test_helpers.bash for why "main" is used
# in tests.

setup() {
    true
}

teardown() {
    true
}


@test "'psec help' can load all entry points" {
    run $PSEC help 2>&1
    refute_output --partial "Could not load EntryPoint"
}

@test "'psec --version' works" {
    run $PSEC --version
    assert_output --partial "main"
}

@test "'psec --help' shows usage" {
    run $PSEC --help
    assert_output --partial 'Python secrets management app'
}

# vim: set ts=4 sw=4 tw=0 et :
