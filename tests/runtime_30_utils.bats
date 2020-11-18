load test_helper

# Ensure cleanup on interrupt
trap "rm -rf ${TEST_DIR}_{keep,donotkeep}" EXIT INT TERM QUIT

# Use: files_count /path/to/dir "*.type"
files_count() {
    find $1 -depth 1 -type f -name "${2:-*}" 2>/dev/null | wc -l
}

setup_file() {
    export TEST_FILES_COUNT=$(files_count tests/secrets/secrets.d "*.yml")
    export TEST_DIR=$(mktemp bats_XXXXXXXX)
    for TEST in keep donotkeep; do
        mkdir -p ${TEST_DIR}_${TEST}
        cp tests/secrets/secrets.d/*.yml ${TEST_DIR}_${TEST}/
    done
}

teardown_file() {
    rm -rf ${TEST_DIR}_{keep,donotkeep}
}

@test "'psec utils yaml-to-json' from stdin works" {
    run $PSEC utils yaml-to-json < $(echo ${TEST_DIR}_keep/*.yml | cut -d' ' -f1)
    assert_output --partial 'Variable'
    tree ${TEST_DIR}_keep >&2
    assert_equal $(files_count ${TEST_DIR}_keep "*.yml") ${TEST_FILES_COUNT}
}

@test "'psec utils yaml-to-json' converts all YAML files in directory" {
    run bash -c "$PSEC utils yaml-to-json ${TEST_DIR}_keep 2>&1 | grep -c converting"
    assert_output "${TEST_FILES_COUNT}"
}

@test "'psec utils yaml-to-json --convert --keep-original' works" {
    run $PSEC utils yaml-to-json --convert --keep-original ${TEST_DIR}_keep
    tree ${TEST_DIR}_keep >&2
    assert_equal $(files_count ${TEST_DIR}_keep "*.json") ${TEST_FILES_COUNT}
    assert_equal $(files_count ${TEST_DIR}_keep "*.yml") ${TEST_FILES_COUNT}
}

@test "'psec utils yaml-to-json --convert' works" {
    run $PSEC utils yaml-to-json --convert ${TEST_DIR}_donotkeep
    tree ${TEST_DIR}_donotkeep >&2
    assert_equal $(files_count ${TEST_DIR}_donotkeep "*.json") ${TEST_FILES_COUNT}
    assert_equal $(files_count ${TEST_DIR}_donotkeep "*.yml") 0
}

# vim: set ts=4 sw=4 tw=0 et :
