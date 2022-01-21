load test_helper

setup_file() {
    remove_basedir
}

setup() {
    remove_basedir
}

teardown() {
    remove_basedir
}

teardown_file() {
    remove_basedir
}

@test "Running 'psec environments list' before 'psec init' fails" {
    run $PSEC environments list 2>&1 </dev/null
    assert_failure
    [ ! -f "${D2_SECRETS_BASEDIR}/.psec" ]
    assert_output --partial "to initialize secrets storage"
}

@test "'psec -v init' creates secrets basedir" {
    run $PSEC init 2>&1
    assert_success
    assert_output --partial "initialized secrets storage in"
    [ -f ${D2_SECRETS_BASEDIR}/.psec ]
}

@test "'psec init' twice does not cause errors" {
    run $PSEC init 2>&1
    run $PSEC init 2>&1
    assert_success
    assert_output --partial "is enabled for secrets storage"
}

@test "'psec -v --init environments create testenv ...' works {
    run $PSEC --init environments create testenv --clone-from tests/secrets.d 1>&2
    assert_success
    assert_output --partial "does not exist"
    assert_output --partial "initialized secrets storage"
    assert_output --partial "created"
    [ -f ${D2_SECRETS_BASEDIR}/.psec ]
}

# vim: set ts=4 sw=4 tw=0 et :
