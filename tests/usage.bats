load test_helper


@test "'psec --help' shows usage" {
    run $PSEC --help
    assert_output_contains 'Python secrets management app'
}

# vim: set ts=4 sw=4 tw=0 et :
