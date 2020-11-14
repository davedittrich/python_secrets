load test_helper

export OAUTH_COUNT=$(grep Variable secrets/secrets.d/oauth.json | wc -l)
export JENKINS_COUNT=$(grep Variable secrets/secrets.d/jenkins.json | wc -l)

setup() {
    run $PSEC environments create --clone-from secrets 1>&2
}

teardown() {
    rm -rf /tmp/.secrets/bats
}

@test "'psec groups list' contains 'jenkins'" {
    run $PSEC groups list
    assert_output --partial jenkins
}

@test "'psec groups show jenkins' contains $JENKINS_COUNT items" {
    bash -c "$PSEC -q groups show jenkins -f csv"  >&2
    run bash -c "$PSEC -q groups show jenkins -f csv | grep -c jenkins"
    assert_output "$JENKINS_COUNT"
}

@test "'psec groups list' contains 'oauth'" {
    run $PSEC groups list
    assert_output --partial oauth
}

@test "'psec groups show oauth' contains $OAUTH_COUNT items" {
    bash -c "$PSEC -q groups show oauth -f csv"  >&2
    run bash -c "$PSEC -q groups show oauth -f csv | grep -c oauth"
    assert_output "$OAUTH_COUNT"
}

# vim: set ts=4 sw=4 tw=0 et :
