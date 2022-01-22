load test_helper

setup() {
    ensure_basedir
    run $PSEC --init environments create $D2_ENVIRONMENT --clone-from tests/secrets.d 1>&2
}

teardown() {
    remove_basedir
}

@test "'psec --umask -1 run ...' fails" {
    run $PSEC --umask -1 run umask 1>&2
    assert_failure
}

@test "'psec --umask 007 run ...' fails" {
    run $PSEC --umask 077 run umask 1>&2
    assert_failure
}

@test "'psec --umask 0o7777 run ...' fails" {
    run $PSEC --umask 0o7777 run umask 1>&2
    assert_failure
}

@test "'psec --umask 0o007 succeeds'" {
    run $PSEC -e testenv --umask 0o007 run umask 1>&2
    assert_output "0007"
}

@test "'psec --umask 0o777 succeeds'" {
    run $PSEC -e testenv --umask 0o777 run umask 1>&2
    assert_output "0777"
}

@test "'psec -E run -- bash -c env' exports PYTHON_SECRETS_ENVIRONMENT" {
    # Nesting processes to really, really, prove environment variable is passed.
    run $PSEC -E run -- bash -c "(env | grep PYTHON_SECRETS_ENVIRONMENT)"
    assert_success
    assert_output --partial PYTHON_SECRETS_ENVIRONMENT
}

@test "'psec -E run sleep 1' succeeds" {
    run $PSEC -E run sleep 1 2>&1
    assert_success
}

@test "'psec --elapsed run sleep 1' succeeds" {
    run $PSEC --elapsed run sleep 1 2>&1
    assert_success
    assert_output --partial elapsed
}

@test "'psec -e NOSUCHENVIRONMENT --elapsed run sleep 1' succeeds" {
    run $PSEC -e NOSUCHENVIRONMENT --elapsed run sleep 1 2>&1
    assert_success
    assert_output --partial elapsed
}

@test "'psec -E -e NOSUCHENVIRONMENT --elapsed run sleep 1' fails" {
    run $PSEC -E -e NOSUCHENVIRONMENT --elapsed run sleep 1 2>&1
    assert_failure
    assert_output --partial 'does not exist'
}

# vim: set ts=4 sw=4 tw=0 et :
