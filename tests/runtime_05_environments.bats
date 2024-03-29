load test_helper

setup_file() {
    clean_environments alias clone testenv ${D2_ENVIRONMENT}renamed
}

setup() {
    run $PSEC --init environments create --clone-from tests/secrets.d 1>&2
}

teardown() {
    clean_environments alias clone testenv ${D2_ENVIRONMENT}renamed
    remove_basedir
}

@test "'psec environments delete ${D2_ENVIRONMENT} --force' deletes environment" {
    run $PSEC -vvv environments delete ${D2_ENVIRONMENT} --force 1>&2
    assert_success
    assert_output --partial "[+] deleted directory path"
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT ]
}

@test "'psec environments path --tmpdir' succeeds when $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT exists" {
    run $PSEC environments path --tmpdir 1>&2
    assert_output --partial "$D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp"
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp ]
}

# @test "'psec environments path --tmpdir' fails when $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT does not exist" {
#     run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
#     run $PSEC environments path --tmpdir 1>&2
#     assert_failure
#     assert_output --partial "does not exist"
#     [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp ]
# }

@test "'psec environments path --tmpdir --create' succeeds when $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT does not exist" {
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
    run $PSEC environments path --tmpdir --create 1>&2
    assert_success
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

@test "'psec environments create --clone-from tests/secrets.d' using default works" {
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
    run $PSEC -vvv environments create --clone-from tests/secrets.d 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    run bash -c "cd $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT && tree secrets.d" </dev/null
    assert_output "secrets.d
├── consul.json
├── hypriot.json
├── jenkins.json
├── myapp.json
├── oauth.json
└── trident.json

1 directory, 6 files"
}

@test "'psec environments create testenv --clone-from tests/secrets.d' works" {
    run $PSEC -vvv environments create testenv --clone-from tests/secrets.d 1>&2
    [ -d $D2_SECRETS_BASEDIR/testenv/secrets.d ]
    run bash -c "cd $D2_SECRETS_BASEDIR/testenv && tree secrets.d" </dev/null
    assert_output "secrets.d
├── consul.json
├── hypriot.json
├── jenkins.json
├── myapp.json
├── oauth.json
└── trident.json

1 directory, 6 files"
}

@test "'psec -e testenv environments create --clone-from tests/secrets.d' works" {
    run $PSEC -vvv -e testenv environments create --clone-from tests/secrets.d 1>&2
    [ -d $D2_SECRETS_BASEDIR/testenv/secrets.d ]
    run bash -c "cd $D2_SECRETS_BASEDIR/testenv && tree secrets.d" </dev/null
    assert_output "secrets.d
├── consul.json
├── hypriot.json
├── jenkins.json
├── myapp.json
├── oauth.json
└── trident.json

1 directory, 6 files"
}

@test "'psec environments create testenv2 --clone-from testenv' works" {
    run $PSEC -q environments create testenv --clone-from tests/secrets.d 1>&2
    run $PSEC -vvv environments create testenv2 --clone-from testenv 1>&2
    assert_success
    [ -d $D2_SECRETS_BASEDIR/testenv2/secrets.d ]
}

@test "'psec environments create --clone-from tests/secrets.d/jenkins.json' works" {
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
    run $PSEC -vvv environments create --clone-from tests/secrets.d/jenkins.json 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    run bash -c "cd $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT && tree secrets.d" </dev/null
    assert_output "secrets.d
└── jenkins.json

1 directory, 1 file"
}

@test "'psec environments create --clone-from /tmp' fails" {
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
    run $PSEC -vvv environments create --clone-from /tmp 1>&2
    assert_failure
    assert_output --partial "does not exist"
}

@test "'psec environments create --clone-from nosuchenvironment' fails" {
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
    run $PSEC -vvv environments create --clone-from nosuchenvironment 1>&2
    assert_failure
    assert_output --partial "does not exist"
}

@test "'psec environments create --alias alias $D2_ENVIRONMENT' creates link $D2_SECRETS_BASEDIR/alias" {
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    [ -L $D2_SECRETS_BASEDIR/alias ]
}

@test "'psec environments create --alias alias' works" {
    run $PSEC environments create --alias alias 1>&2
    assert_success
    assert_output --partial "[+] environment 'alias' aliased to"
}

@test "'psec environments delete alias --force' deletes alias" {
    run $PSEC environments create --alias alias 1>&2
    run $PSEC environments delete alias --force 1>&2
    assert_success
    assert_output --partial "[+] deleted alias"
    [ ! -L $D2_SECRETS_BASEDIR/alias ]
}

@test "'psec environments create --alias alias environmentthatdoesnotexist' fails" {
    run $PSEC environments create --alias alias environmentthatdoesnotexist 1>&2
    assert_failure
}

@test "'psec environments create --alias alias $D2_ENVIRONMENT anotherarg' fails" {
    run $PSEC environments create --alias alias $D2_ENVIRONMENT anotherarg 1>&2
    assert_failure
}

@test "'psec environments path' works properly" {
    run $PSEC environments path configs exists
    assert_output "$D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/configs/exists"
}

@test "'psec environments path --exists ...' works properly" {
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
    run $PSEC environments delete ${D2_ENVIRONMENT} --force 1>&2
    run $PSEC environments list
    assert_failure
    assert_output ''
}

@test "'psec -d /this/is/not/a/real/directory environments list' fails" {
    run $PSEC -d /this/is/not/a/real/directory environments list 1>&2
    assert_failure
    assert_output --partial "does not exist"
}

@test "'psec -d /tmp environments list' fails" {
    run $PSEC -d /tmp environments list 1>&2
    assert_failure
    assert_output --partial "is not valid"
}

@test "'psec environments list' works" {
    run $PSEC environments list -f value
    assert_output "${D2_ENVIRONMENT} Yes"
    run $PSEC -vvv environments create clone --clone-from tests/secrets.d 1>&2
    run $PSEC environments list -f value
    assert_output "${D2_ENVIRONMENT} Yes
clone No"
}

@test "'psec -d $D2_SECRETS_BASEDIR environments list' works" {
    #
    # Force unsetting of environment variable (but still use same value
    # for command line argument) for this specific test.
    #
    BASEDIR=$D2_SECRETS_BASEDIR
    run bash -c "unset D2_SECRETS_BASEDIR; $PSEC -d $BASEDIR environments list -f value"
    assert_output "${D2_ENVIRONMENT} Yes"
}

@test "'psec environments list' does not show aliases" {
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    run $PSEC environments list
    refute_output --partial 'AliasFor'
}

@test "'psec environments list --aliasing' show aliases" {
    run $PSEC environments create --alias alias $D2_ENVIRONMENT 1>&2
    run $PSEC environments list
    refute_output --partial 'AliasFor'
}

@test "'psec environments rename $D2_ENVIRONMENT ${D2_ENVIRONMENT}renamed' renames environment" {
    run $PSEC -vvv environments rename $D2_ENVIRONMENT ${D2_ENVIRONMENT}renamed 1>&2
    [ ! -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
    [ -d $D2_SECRETS_BASEDIR/${D2_ENVIRONMENT}renamed/secrets.d ]
}

# vim: set ts=4 sw=4 tw=0 et :
