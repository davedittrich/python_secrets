load test_helper

teardown() {
    rm -rf /tmp/.secrets
}

@test "'psec environments path --tmpdir' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp" {
    run $PSEC environments path --tmpdir 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp ]
}

@test "'psec environments path configs sub --create' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub" {
    run $PSEC environments path configs sub --create 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub ]
}

@test "'psec environments path configs sub --exists' does not create $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub" {
    run $PSEC environments path configs sub --exists 1>&2
    assert_failure
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub ]
}

@test "'psec environments create --clone-from secrets' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d" {
    run $PSEC -vvv environments create --clone-from secrets 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
}

@test "'psec environments path' works properly" {
    run $PSEC environments path configs exists
    assert_output "$D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists"
}

@test "'psec environments path --exists ...' works properly" {
    run $PSEC -vvv environments create --clone-from secrets 1>&2
    run $PSEC environments path configs exists --exists
    assert_failure
    mkdir -p $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists
    run $PSEC environments path configs exists --exists
    assert_success
    rmdir $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists
    run $PSEC environments path configs exists --exists
    assert_failure
}

# TODO(dittrich): Disabling as the new Bullet feature doesn't time out. :(
# @test "'psec environments delete testenv' produces error message" {
#     run $PSEC -vvv environments create testenv --clone-from secrets 1>&2
#     run $PSEC -vvv environments delete testenv 1>&2
#     assert_output --partial 'must use "--force" flag to delete an environment'
# }

@test "'psec environments delete --force testenv' removes $D2_SECRETS_BASEDIR/testenv" {
    run $PSEC -vvv environments -e testenv create --clone-from secrets 1>&2
    run $PSEC -vvv environments delete --force testenv 1>&2
    [ ! -d $D2_SECRETS_BASEDIR/testenv ]
}

@test "'psec environments list' does not show aliases" {
    run $PSEC environments create --clone-from secrets 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    run $PSEC environments list
    refute_output --partial 'AliasFor'
}

@test "'psec environments list --aliasing' show aliases" {
    run $PSEC environments create --clone-from secrets 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    run $PSEC environments list
    refute_output --partial 'AliasFor'
}

@test "'psec environments rename $D2_ENVIRONMENT ${D2_ENVIRONMENT}renamed' renames environment" {
    run $PSEC -vvv environments create --clone-from secrets 1>&2
    run $PSEC -vvv environments rename $D2_ENVIRONMENT ${D2_ENVIRONMENT}renamed 1>&2
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    [ -d $D2_SECRETS_BASEDIR/${D2_ENVIRONMENT}renamed/secrets.d ]
}

@test "'psec environments create --clone-from nosuchsecrets' fails" {
    run $PSEC environments create --clone-from nosuchsecrets 1>&2
    assert_failure
}

@test "'psec environments create --alias alias $D2_ENVIRONMENT' creates link $D2_SECRETS_BASEDIR/alias" {
    run $PSEC environments create --clone-from secrets 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    [ -L $D2_SECRETS_BASEDIR/alias ]
}

@test "'psec environments create --alias alias' fails" {
    run $PSEC environments create --alias alias 1>&2
    assert_failure
}

@test "'psec environments create --alias alias environmentthatdoesnotexist' fails" {
    run $PSEC environments create --alias alias environmentthatdoesnotexist 1>&2
    assert_failure
}

@test "'psec environments create --alias alias $D2_ENVIRONMENT anotherarg' fails" {
    run $PSEC environments create --clone-from secrets 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT anotherarg 1>&2
    assert_failure
}

# vim: set ts=4 sw=4 tw=0 et :
