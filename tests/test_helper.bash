export OS=$(uname -s)
# Sets D2_ENVIRONMENT and D2_SECRETS_BASEDIR environment variables.
# source test-environment.bash
export D2_ENVIRONMENT="batstest"
export D2_SECRETS_BASEDIR="/tmp/.secrets_bats$$"
export PYTHONPATH=$(pwd)
export PSEC="python -m psec.__main__ --debug"

# By default, cleans up the standard environment. Also use to
# clean up any alternative environments created during testing
# by specifying them as arguments when calling the function.

function ensure_basedir() {
    if [ ! -f "${D2_SECRETS_BASEDIR}" ]; then
        mkdir -p "${D2_SECRETS_BASEDIR}"
        chmod 700 "${D2_SECRETS_BASEDIR}"
        touch "${D2_SECRETS_BASEDIR}/.psec"
        chmod 600 "${D2_SECRETS_BASEDIR}/.psec"
    fi
}

function remove_basedir() {
    if [ -d "${D2_SECRETS_BASEDIR}" ]; then
       rm -rf "${D2_SECRETS_BASEDIR}"
    fi
}


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
