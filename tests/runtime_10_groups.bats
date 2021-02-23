load test_helper

export OAUTH_COUNT=$(grep -c Variable tests/secrets.d/oauth.json)
export JENKINS_COUNT=$(grep -c Variable tests/secrets.d/jenkins.json)

setup() {
    run $PSEC environments create --clone-from tests/secrets.d 1>&2
}

teardown() {
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
}

@test "'psec groups path' returns ${D2_SECRETS_BASEDIR}/${D2_ENVIRONMENT}/secrets.d" {
    run $PSEC groups path
    assert_success
    assert_output "${D2_SECRETS_BASEDIR}/${D2_ENVIRONMENT}/secrets.d"
}

@test "'psec groups list' contains 'jenkins' and 'oauth'" {
    run $PSEC groups list
    assert_success
    assert_output --partial jenkins
    assert_output --partial oauth
}

@test "'psec groups show nosuchgroup' fails" {
    run $PSEC groups show nosuchgroup
    assert_failure
    assert_output ""
}

@test "'psec groups show jenkins' contains $JENKINS_COUNT item(s)" {
    bash -c "$PSEC -q groups show jenkins -f csv"  >&2
    run bash -c "$PSEC -q groups show jenkins -f csv | grep -c jenkins"
    assert_success
    assert_output "$JENKINS_COUNT"
}

@test "'psec groups show oauth' contains $OAUTH_COUNT item(s)" {
    bash -c "$PSEC -q groups show oauth -f csv"  >&2
    run bash -c "$PSEC -q groups show oauth -f csv | grep -c oauth"
    assert_success
    assert_output "$OAUTH_COUNT"
}

@test "'psec groups create emptygroup' creates an empty group" {
    run $PSEC groups create emptygroup
    assert_success
    assert_output --partial 'creating'
    run echo $($PSEC -q groups path)/emptygroup.json >&2
    [ -f $($PSEC -q groups path)/emptygroup.json ]
    run $PSEC groups show emptygroup -f csv
    assert_failure
    assert_output ''
}

@test "'psec groups create emptygroup' twice fails" {
    run $PSEC groups create emptygroup
    run $PSEC groups create emptygroup
    assert_failure
    assert_output --partial 'already exists'
}

@test "'psec groups create --clone-from tests/gosecure.json' works" {
    run $PSEC groups create --clone-from tests/gosecure.json
    assert_success
    assert_output --partial 'creating'
    [ -f $($PSEC -q groups path)/gosecure.json ]
}

@test "'psec groups create newgroup --clone-from tests/gosecure.json' works" {
    run $PSEC groups create newgroup --clone-from tests/gosecure.json
    assert_success
    assert_output --partial 'creating'
    [ ! -f $($PSEC groups path)/gosecure.json ]
    [ -f $($PSEC groups path)/newgroup.json ]
}

@test "'psec groups create newgroup --clone-from tests/gosecure.json' twice fails" {
    run $PSEC groups create newgroup --clone-from tests/gosecure.json
    assert_success
    assert_output --partial 'creating'
    run $PSEC groups create newgroup --clone-from tests/gosecure.json
    assert_failure
    assert_output --partial "already exists"
}

@test "'psec groups create --clone-from nosuchenv' fails" {
    run $PSEC groups create --clone-from nosuchenv
    assert_failure
    assert_output --partial "please specify which group"
}

@test "'psec groups delete oauth --force' works" {
    run $PSEC groups delete oauth --force
    assert_success
    assert_output --partial "deleted secrets group 'oauth'"
}

@test "'psec groups delete oauth' without TTY fails" {
    run $PSEC groups delete oauth </dev/null
    assert_failure
    assert_output --partial 'must use "--force" flag'
}

# vim: set ts=4 sw=4 tw=0 et :
