load test_helper

# Use: files_count /path/to/dir "*.type"
files_count() {
    find "$1" -depth 1 -type f -name "${2:-*}" 2>/dev/null | wc -l
}

export TEST_FILES_COUNT="$(files_count tests/yamlsecrets/secrets.d '*.yml')"
export KEEP_DIR="${BATS_TMPDIR}/bats_keep"
export DONOTKEEP_DIR="${BATS_TMPDIR}/bats_donotkeep"

# TODO(dittrich): Some odd bug in bats-core v1.2.1 causes failures
# for all defined tests:
#
# $ bats tests/runtime_30_utils.bats
#    bats warning: Executed 0 instead of expected 4 tests
#
# Had to back off to using v1.2.0 following steps defined in:
# https://zoltanaltfatter.com/2017/09/07/Install-a-specific-version-of-formula-with-homebrew/

# Ensure cleanup on interrupt
trap "rm -rf ${KEEP_DIR} ${DONOTKEEP_DIR}" EXIT INT TERM QUIT

setup() {
    for DIR in ${KEEP_DIR} ${DONOTKEEP_DIR}; do
        rm -rf ${DIR}
        mkdir -p ${DIR}
        cp tests/yamlsecrets/secrets.d/*.yml ${DIR}/
    done
    run $PSEC --init environments create $D2_ENVIRONMENT --clone-from tests/secrets.d 1>&2
}

teardown() {
    rm -rf ${KEEP_DIR} ${DONOTKEEP_DIR}
    remove_basedir
}

@test "Setting up ${KEEP_DIR} worked" {
    assert_equal "$(files_count ${DONOTKEEP_DIR} '*.yml')" "${TEST_FILES_COUNT}"
}

@test "'psec utils yaml-to-json ${KEEP_DIR}/jenkins.yml' works" {
    run $PSEC utils yaml-to-json ${KEEP_DIR}/jenkins.yml
    assert_output '[
  {
    "Variable": "jenkins_admin_password",
    "Type": "password",
    "Prompt": "Password for Jenkins \"admin\" account"
  }
]'
    assert_success
}

@test "'psec utils yaml-to-json --convert ${DONOTKEEP_DIR}/jenkins.yml' works" {
    run $PSEC utils yaml-to-json --convert ${DONOTKEEP_DIR}/jenkins.yml
    assert_output --partial '[+] converting'
    assert_success
    [ -f ${DONOTKEEP_DIR}/jenkins.json ]
    [ ! -f ${DONOTKEEP_DIR}/jenkins.yml ]
}

@test "'psec utils yaml-to-json --convert --keep-original ${KEEP_DIR}/jenkins.yml' works" {
    run $PSEC utils yaml-to-json --convert --keep-original ${KEEP_DIR}/jenkins.yml
    assert_output --partial '[+] converting'
    assert_success
    [ -f ${KEEP_DIR}/jenkins.json ]
    [ -f ${KEEP_DIR}/jenkins.yml ]
}

@test "'psec utils yaml-to-json' from stdin works" {
    run bash -c "cat ${KEEP_DIR}/oauth.yml | $PSEC utils yaml-to-json -"
    assert_output --partial '
  {
    "Variable": "google_oauth_username",
    "Type": "string",
    "Prompt": "Google OAuth2 username"
  }'
    assert_success
    [ ! -f ${KEEP_DIR}/oauth.json ]
    [ -f ${KEEP_DIR}/oauth.yml ]
}

@test "'psec utils yaml-to-json --convert ${DONOTKEEP_DIR}' works" {
    run $PSEC utils yaml-to-json --convert ${DONOTKEEP_DIR}
    assert_success
    assert_equal "$(files_count ${DONOTKEEP_DIR} '*.json')" "${TEST_FILES_COUNT}"
    assert_equal "$(files_count ${DONOTKEEP_DIR} '*.yml')" "0"
}

@test "'psec utils yaml-to-json --convert --keep-original ${KEEP_DIR}' works" {
    run $PSEC utils yaml-to-json --convert --keep-original ${KEEP_DIR}
    assert_success
    assert_equal "$(files_count ${KEEP_DIR} '*.json')" "${TEST_FILES_COUNT}"
    assert_equal "$(files_count ${KEEP_DIR} '*.yml')" "${TEST_FILES_COUNT}"
}


# vim: set ts=4 sw=4 tw=0 et :
