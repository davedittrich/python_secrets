load test_helper

setup() {
    run $PSEC environments create $D2_ENVIRONMENT --clone-from tests/secrets.d 1>&2
}

teardown() {
    run $PSEC environments delete $D2_ENVIRONMENT --force 1>&2
}

@test "'psec run -E -- bash -c env' exports PYTHON_SECRETS_ENVIRONMENT" {
    # Nesting processes to really, really, prove environment variable is passed.
    run $PSEC run -E -- bash -c "(env | grep PYTHON_SECRETS_ENVIRONMENT)"
    assert_success
    assert_output --partial PYTHON_SECRETS_ENVIRONMENT
}

# vim: set ts=4 sw=4 tw=0 et :
