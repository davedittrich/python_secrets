load test_helper

export TEST_PASSWORD="mummy_unbaked_tabby_thespian"

setup() {
    run $PSEC environments create --clone-from secrets 1>&2
}

teardown() {
    rm -rf /tmp/.secrets/bats
}

@test "'psec secrets set jenkins_admin_password=$TEST_PASSWORD' sets variable properly" {
    run $PSEC secrets set jenkins_admin_password=$TEST_PASSWORD
    run $PSEC secrets show jenkins_admin_password --no-redact -f csv
    assert_output --partial "$TEST_PASSWORD"
}

@test "'psec secrets path' from env var works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC secrets path
    assert_output --partial "/fromenv/secrets.yml"
}

@test "'psec -e fromoption secrets path' works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC -e fromoption secrets path
    assert_output --partial "/fromoption/secrets.yml"
}

@test "'psec secrets path fromarg' works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC secrets path fromarg
    assert_output --partial "/fromarg/secrets.yml"
}

@test "'psec secrets path' from directory works properly" {
    [ ! -f .python_secrets_environment ]
    run $PSEC secrets path
    assert_output --partial "/bats/secrets.yml"
}


# vim: set ts=4 sw=4 tw=0 et :
