export OS=$(uname -s)
export PYTHONPATH=$(pwd)
export PSEC="python3 -m python_secrets.main"
export D2_ENVIRONMENT="bats"
export D2_SECRETS_BASEDIR="/tmp/.secrets"

load ../../bats-assert/all

# vim: set ts=4 sw=4 tw=0 et :
