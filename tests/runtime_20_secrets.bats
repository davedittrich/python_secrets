load test_helper

# Use: files_count /path/to/dir "*.type"
files_count() {
    find $1 -depth 1 -type f -name "${2:-*}" 2>/dev/null | wc -l
}

export TEST_PASSWORD="mummy_unbaked_tabby_thespian"

trap "rm -rf ${TEST_DIR}_{keep,donotkeep}" EXIT INT TERM QUIT

setup_file() {
    export TEST_FILES_COUNT=$(files_count tests/secrets/secrets.d "*.yml")
    export TEST_DIR=$(mktemp bats_XXXXXXXX)
    for TEST in keep donotkeep; do
        mkdir -p ${TEST_DIR}_${TEST}
        cp tests/secrets/secrets.d/*.yml ${TEST_DIR}_${TEST}/
    done
}

setup() {
    run $PSEC environments create --clone-from secrets 1>&2
}

teardown() {
    rm -rf /tmp/.secrets/bats
}

teardown_file() {
    rm -rf ${TEST_DIR}_{keep,donotkeep}
}

@test "'psec secrets set jenkins_admin_password=$TEST_PASSWORD' sets variable properly" {
    run $PSEC secrets set jenkins_admin_password=$TEST_PASSWORD
    run $PSEC secrets show jenkins_admin_password --no-redact -f csv
    assert_output --partial "$TEST_PASSWORD"
}

@test "'psec secrets path' from env var works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC secrets path
    assert_output --partial "/fromenv/secrets.json"
}

@test "'psec -e fromoption secrets path' works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC -e fromoption secrets path
    assert_output --partial "/fromoption/secrets.json"
}

@test "'psec secrets path fromarg' works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC secrets path fromarg
    assert_output --partial "/fromarg/secrets.json"
}

@test "'psec secrets path' from directory works properly" {
    [ ! -f .python_secrets_environment ]
    run $PSEC secrets path
    assert_output --partial "/bats/secrets.json"
}

@test "'psec utils yaml-to-json --keep-original' works" {
    run $PSEC utils yaml-to-json --keep-original ${TEST_DIR}_keep
    tree ${TEST_DIR}_keep >&2
    assert_equal $(files_count ${TEST_DIR}_keep "*.json") ${TEST_FILES_COUNT}
    assert_equal $(files_count ${TEST_DIR}_keep "*.yml") ${TEST_FILES_COUNT}
}

@test "'psec utils yaml-to-json' works" {
    run $PSEC utils yaml-to-json ${TEST_DIR}_donotkeep
    tree ${TEST_DIR}_donotkeep >&2
    assert_equal $(files_count ${TEST_DIR}_donotkeep "*.json") ${TEST_FILES_COUNT}
    assert_equal $(files_count ${TEST_DIR}_donotkeep "*.yml") 0
}

# vim: set ts=4 sw=4 tw=0 et :
