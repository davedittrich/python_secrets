export OS=$(uname -s)
export PYTHONPATH=$(pwd)
export D2_ENVIRONMENT="bats"
export D2_SECRETS_BASEDIR="/tmp/.secrets"
export PSEC="python3 -m psec.main --debug"

load ../../bats-support/load
load ../../bats-assert-1/load

# vim: set ts=4 sw=4 tw=0 et :
