load test_helper

teardown() {
    rm -rf /tmp/.secrets
}

@test "'psec --umask -1 fails'" {
    run $PSEC --umask -1 run umask 1>&2
    assert_failure
}

@test "'psec --umask 007 fails'" {
    run $PSEC --umask 077 run umask 1>&2
    assert_failure
}

@test "'psec --umask 0o7777 fails'" {
    run $PSEC --umask 0o7777 run umask 1>&2
    assert_failure
}

@test "'psec --umask 0o007 succeeds'" {
    # Needs an environment to work properly.
    run $PSEC -vvv environments create testenv --clone-from tests/secrets.d 1>&2
    run $PSEC -e testenv --umask 0o007 run umask 1>&2
    assert_output "0007"
}

@test "'psec --umask 0o777 succeeds'" {
    # Needs an environment to work properly.
    run $PSEC -vvv environments create testenv --clone-from tests/secrets.d 1>&2
    run $PSEC -e testenv --umask 0o777 run umask 1>&2
    assert_output "0777"
}

# vim: set ts=4 sw=4 tw=0 et :
