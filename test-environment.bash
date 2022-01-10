# Source this file to mimic test and VSCode debugging launch settings.
# That's what tests/test_helper.sh does as well.

# Put all test environments in /tmp to avoid messing with any
# real environments.  This directory is also used in the
# .vscode/launch.json file for more consistent testing.
export D2_ENVIRONMENT="psectest"
export D2_SECRETS_BASEDIR="/tmp/.psecsecrets"
