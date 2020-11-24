load test_helper

# Use: files_count /path/to/dir "*.type"
files_count() {
    find "$1" -depth 1 -type f -name "${2:-*}" 2>/dev/null | wc -l
}

# TODO(dittrich): Some odd bug in bats-core v1.2.1 causes failures
# for all defined tests:
#
# $ bats tests/runtime_30_utils.bats
#    bats warning: Executed 0 instead of expected 4 tests
#
# Had to back off to using v1.2.0 following steps defined in:
# https://zoltanaltfatter.com/2017/09/07/Install-a-specific-version-of-formula-with-homebrew/

export TEST_FILES_COUNT="$(files_count tests/secrets.d '*.yml')"
export TEST_DIR="/tmp/$(mktemp bats_XXXXXXXX)"

# Ensure cleanup on interrupt
trap "rm -rf ${TEST_DIR}_{keep,donotkeep}" EXIT INT TERM QUIT

setup_file() {
    for TEST in keep donotkeep; do
        mkdir -p ${TEST_DIR}_${TEST}
        cp tests/secrets/secrets.d/*.yml ${TEST_DIR}_${TEST}/
    done
}

teardown_file() {
    rm -rf ${TEST_DIR}_{keep,donotkeep}
}

@test "'psec utils yaml-to-json' from stdin works" {
    run $PSEC utils yaml-to-json < tests/secrets/secrets.d/jenkins.yml
    assert_success
    assert_output --partial 'Variable'
}

@test "'psec utils yaml-to-json' converts all YAML files in directory" {
    run bash -c "$PSEC utils yaml-to-json ${TEST_DIR}_keep 2>&1 | grep -c converting"
    assert_output "${TEST_FILES_COUNT}"
}

@test "'psec utils yaml-to-json --convert --keep-original' works" {
    run $PSEC utils yaml-to-json --convert --keep-original ${TEST_DIR}_keep
    assert_equal "$(files_count ${TEST_DIR}_keep '*.json')" "${TEST_FILES_COUNT}"
    assert_equal "$(files_count ${TEST_DIR}_keep '*.yml')" "${TEST_FILES_COUNT}"
}

@test "'psec utils yaml-to-json --convert' works" {
    run $PSEC utils yaml-to-json --convert ${TEST_DIR}_donotkeep
    assert_equal "$(files_count ${TEST_DIR}_donotkeep '*.json')" "${TEST_FILES_COUNT}"
    assert_equal "$(files_count ${TEST_DIR}_donotkeep '*.yml')" "0"
}

# vim: set ts=4 sw=4 tw=0 et :
