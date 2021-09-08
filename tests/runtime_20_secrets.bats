load test_helper

export TEST_PASSWORD="mummy_unbaked_tabby_thespian"

setup() {
    run $PSEC environments create $D2_ENVIRONMENT --clone-from tests/secrets.d 1>&2
}

teardown() {
    run $PSEC environments delete $D2_ENVIRONMENT --force 1>&2
}

@test "'psec secrets set' without arguments fails" {
    run $PSEC secrets set 2>&1
    assert_failure
    assert_output --partial "no secrets specified"
}

@test "'psec secrets set jenkins_admin_password=$TEST_PASSWORD' sets variable properly" {
    run $PSEC secrets set jenkins_admin_password=$TEST_PASSWORD
    run $PSEC secrets show jenkins_admin_password --no-redact -f csv
    assert_output --partial "$TEST_PASSWORD"
}

@test "'psec secrets generate sets variables properly" {
    run $PSEC secrets show --no-redact consul_key hypriot_password myapp_client_psk -f value
    assert_output 'hypriot_password None hypriot_password
consul_key None consul_key
myapp_client_psk None DEMO_client_psk'
    run $PSEC secrets generate consul_key hypriot_password myapp_client_psk
    run $PSEC secrets get consul_key
    assert_output --partial "="
    run $PSEC secrets show --no-redact hypriot_password
    refute_output 'None'
    run $PSEC secrets get myapp_client_psk
    assert_output 'None'
}

@test "'psec secrets set --from-options' sets variables properly" {
    run $PSEC secrets set --from-options
    run $PSEC secrets get hypriot_hostname
    assert_output "hypriot"
    run $PSEC secrets get hypriot_user
    assert_output "pirate"
    run $PSEC secrets get hypriot_wifi_country
    assert_output "US"
}

@test "'psec secrets show' table header is correct" {
    run bash -c "$PSEC secrets show -f csv | head -n 1"
    assert_output '"Variable","Value","Export"'
}

@test "'psec secrets describe' table header is correct" {
    run bash -c "$PSEC secrets describe -f csv | head -n 1"
    assert_output '"Variable","Group","Type","Prompt","Options"'
}

@test "'psec secrets path' from env var works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC secrets path
    assert_output --partial "/fromenv/secrets.json"
}

@test "'psec -e fromoption secrets path' works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC -e fromoption secrets path
    assert_output --partial "/fromoption/secrets.json"
}

@test "'psec secrets path fromarg' works properly" {
    D2_ENVIRONMENT=fromenv run $PSEC secrets path fromarg
    assert_output --partial "/fromarg/secrets.json"
}

@test "'psec secrets path' from directory works properly" {
    [ ! -f .python_secrets_environment ]
    run $PSEC secrets path
    assert_output "${D2_SECRETS_BASEDIR}/${D2_ENVIRONMENT}/secrets.json"
}

@test "'psec secrets describe --group jenkins' works properly" {
    run $PSEC secrets describe --group jenkins
    assert_output "+------------------------+---------+----------+--------------------------------------+---------+
| Variable               | Group   | Type     | Prompt                               | Options |
+------------------------+---------+----------+--------------------------------------+---------+
| jenkins_admin_password | jenkins | password | Password for Jenkins 'admin' account | *       |
+------------------------+---------+----------+--------------------------------------+---------+"
}

# TODO(dittrich): This should really fail with $? != 0 if no group.
@test "'psec secrets describe --group nosuchgroup' fails" {
    run $PSEC secrets describe --group nosuchgroup
    assert_output ""
}

@test "'psec secrets create' fails without a TTY" {
    run $PSEC secrets create --group nosuchgroup somevariable </dev/null 2>&1
    assert_failure
    assert_output --partial "TTY"
}

@test "'psec secrets delete --group oauth google_oauth_refresh_token' shrinks file" {
    run grep -q google_oauth_refresh_token $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.json
    assert_success
    run $PSEC secrets show google_oauth_refresh_token -f value
    assert_success
    run bash -c "$PSEC -q groups show oauth -f csv | grep -c oauth"
    assert_output "4"
    run $PSEC secrets delete --group oauth google_oauth_refresh_token --force
    [ -f $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d/oauth.json ]
    run bash -c "$PSEC -q groups show oauth -f csv | grep -c oauth"
    assert_output "3"
    run grep -q google_oauth_refresh_token $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.json
    assert_failure
    run $PSEC secrets show google_oauth_refresh_token -f value
    assert_failure
}

@test "'psec secrets delete --group jenkins jenkins_admin_password' removes group" {
    run $PSEC secrets show jenkins_admin_password -f value
    assert_success
    run $PSEC secrets delete --force --group jenkins jenkins_admin_password 1>&2
    assert_output --partial "deleted empty group"
    run $PSEC secrets show jenkins_admin_password -f value
    assert_failure
    [ ! -f $D2_SECRETS_BASEDIR/$D2_ENVIRONMENT/secrets.d/jenkins.json ]
}

@test "'psec secrets tree $D2_SECRETS_ENVIRONMENT' succeeds" {
    run $PSEC secrets tree $D2_SECRETS_ENVIRONMENT
    assert_output --partial '└'
    assert_success
}

@test "'psec secrets tree environment_that_does_not_exist' fails" {
    run $PSEC secrets tree environment_that_does_not_exist
    assert_failure
}

# vim: set ts=4 sw=4 tw=0 et :
