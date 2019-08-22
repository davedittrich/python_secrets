load test_helper

export COUNT=$(grep Variable secrets/secrets.d/oauth.yml | wc -l)

setup() {
    run $PSEC environments create --clone-from secrets 1>&2
}

teardown() {
    rm -rf /tmp/.secrets/bats
}

@test "'psec groups list' contains 'oauth'" {
    run $PSEC groups list
    assert_output --partial oauth
}

@test "'psec groups show oauth' contains $COUNT items" {
    bash -c "$PSEC -q groups show oauth -f csv"  >&2
    run bash -c "$PSEC -q groups show oauth -f csv | grep oauth | wc -l"
    assert_output "$COUNT"
}

# vim: set ts=4 sw=4 tw=0 et :
