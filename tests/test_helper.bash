export OS=$(uname -s)
# Sets D2_ENVIRONMENT and D2_SECRETS_BASEDIR environment variables.
source test-environment.bash
export PYTHONPATH=$(pwd)
export PSEC="python -m psec.main --debug"

load 'libs/bats-support/load'
load 'libs/bats-assert/load'

# vim: set ts=4 sw=4 tw=0 et :
