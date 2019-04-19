export OS=$(uname -s)
export PYTHONPATH=$(pwd)
export D2_ENVIRONMENT="bats"
export D2_SECRETS_BASEDIR="/tmp/.secrets"
export PSEC="python3 -m python_secrets.main --debug"

load ../../bats-assert/all

# vim: set ts=4 sw=4 tw=0 et :
