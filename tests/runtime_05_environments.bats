load test_helper

teardown() {
    rm -rf /tmp/.secrets/${D2_ENVIRONMENT}
    rm -rf /tmp/.secrets/${D2_ENVIRONMENT}renamed
    rm -rf /tmp/.secrets/{testenv,alias}
}

@test "'psec environments path --tmpdir' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp" {
    run $PSEC environments path --tmpdir 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp ]
}

@test "'psec environments path configs sub --exists' does not create $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub" {
    run $PSEC environments path configs sub --exists 1>&2
    assert_failure
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub ]
}

@test "'psec environments path configs sub --create' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub" {
    run $PSEC environments path configs sub --create 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/sub ]
}

@test "'psec environments create --clone-from tests/secrets.d' works" {
    run $PSEC -vvv environments create --clone-from tests/secrets.d 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    [ $(ls $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d | wc -l) -gt 1 ]
    [ $(ls $(psec groups path) | wc -l) -gt 1 ]
}

@test "'psec environments create --clone-from tests/secrets.d/jenkins.json' works" {
    run $PSEC -vvv environments create --clone-from tests/secrets.d/jenkins.json 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    [ $(ls $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d | wc -l) -eq 1 ]
}

@test "'psec environments create --clone-from /tmp' fails" {
    run $PSEC -vvv environments create --clone-from /tmp 1>&2
    assert_failure
    assert_output --partial "refusing to process"
}

@test "'psec environments create --clone-from nosuchenvironment' fails" {
    run $PSEC -vvv environments create --clone-from nosuchenvironment 1>&2
    assert_failure
    assert_output --partial "does not exist"
}

@test "'psec environments create --alias alias $D2_ENVIRONMENT' creates link $D2_SECRETS_BASEDIR/alias" {
    run $PSEC environments create --clone-from tests/secrets.d 1>&2
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
    run $PSEC environments create --clone-from tests/secrets.d 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT anotherarg 1>&2
    assert_failure
}

@test "'psec environments path' works properly" {
    run $PSEC environments path configs exists
    assert_output "$D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists"
}

@test "'psec environments path --exists ...' works properly" {
    run $PSEC -vvv environments create --clone-from tests/secrets.d 1>&2
    run $PSEC environments path configs exists --exists
    assert_failure
    mkdir -p $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists
    run $PSEC environments path configs exists --exists
    assert_success
    rmdir $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists
    run $PSEC environments path configs exists --exists
    assert_failure
}

@test "'psec environments delete testenv' produces error message" {
    run $PSEC -vvv environments create testenv --clone-from tests/secrets.d 1>&2
    run $PSEC -vvv environments delete testenv 1>&2 </dev/null
    assert_output --partial "must use '--force' flag to delete an environment"
}

@test "'psec environments delete --force testenv' removes $D2_SECRETS_BASEDIR/testenv" {
    run $PSEC -vvv environments -e testenv create --clone-from tests/secrets.d 1>&2
    run $PSEC -vvv environments delete --force testenv 1>&2
    [ ! -d $D2_SECRETS_BASEDIR/testenv ]
}

@test "'psec environments list' with no environments fails" {
    run $PSEC environments list
    assert_failure
    assert_output ''
}

@test "'psec environments list' does not show aliases" {
    run $PSEC environments create --clone-from tests/secrets.d 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    run $PSEC environments list
    refute_output --partial 'AliasFor'
}

@test "'psec environments list --aliasing' show aliases" {
    run $PSEC environments create --clone-from tests/secrets.d 1>&2
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    run $PSEC environments list
    refute_output --partial 'AliasFor'
}

@test "'psec environments rename $D2_ENVIRONMENT ${D2_ENVIRONMENT}renamed' renames environment" {
    run $PSEC -vvv environments create --clone-from tests/secrets.d 1>&2
    run $PSEC -vvv environments rename $D2_ENVIRONMENT ${D2_ENVIRONMENT}renamed 1>&2
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    [ -d $D2_SECRETS_BASEDIR/${D2_ENVIRONMENT}renamed/secrets.d ]
}

# vim: set ts=4 sw=4 tw=0 et :
