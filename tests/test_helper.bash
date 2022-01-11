export OS=$(uname -s)
# Sets D2_ENVIRONMENT and D2_SECRETS_BASEDIR environment variables.
source test-environment.bash
export PYTHONPATH=$(pwd)
export PSEC="python -m psec.__main__ --debug"

trap "clean_bats" SIGINT

function clean_bats() {
    rm -f ${BATS_TEST_DIRNAME}/bats_*
}

# By default, cleans up the standard environment. Also use to
# clean up any alternative environments created during testing
# by specifying them as arguments when calling the function.

function clean_environments() {
    BASEDIR="${D2_SECRETS_BASEDIR:?warning - not set}"
    ENVPATH="${BASEDIR}${D2_ENVIRONMENT:?warning - not set}"
    for environment in $*
    do
        rm -rf ${BASEDIR}/${environment}
    done
}

load 'libs/bats-support/load'
load 'libs/bats-assert/load'

# vim: set ts=4 sw=4 tw=0 et :
