load test_helper

teardown() {
    rm -rf /tmp/.secrets/bats
}

@test "'psec environments path --tmpdir' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp" {
    run $PSEC environments path --tmpdir 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/tmp ]
}

@test "'psec environments create --clone-from secrets' creates $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d" {
    run $PSEC -vvv environments create --clone-from secrets 1>&2
    [ -d $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d ]
}

# vim: set ts=4 sw=4 tw=0 et :
