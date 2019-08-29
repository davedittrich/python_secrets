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

# vim: set ts=4 sw=4 tw=0 et :
