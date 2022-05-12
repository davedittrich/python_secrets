#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_psec.groups
----------------

Tests for `psec.groups` module.
"""

import unittest
import os
import sys

# from unittest.mock import patch

HOST = 'example.com'
HOME = os.path.expanduser('~')
TESTENV = 'pytest'
SECRETS_SUBDIR = 'pytest'
KEYS_SUBDIR = 'keys'


def groups_dir(env=None, basedir=None):
    if env is not None:
        env_str = str(env)
    else:
        env = os.getenv('D2_ENVIRONMENT', None)
        cwd = os.getcwd()
        default_file = os.path.join(cwd, '.python_secrets_environment')
        if os.path.exists(default_file):
            with open(default_file, 'r') as f:
                env_str = f.read().strip()
        else:
            env_str = os.path.basename(cwd)
    basedir = os.getenv('D2_SECRETS_BASEDIR', None)
    if basedir is None:
        basedir = os.path.join(
                HOME,
                'secrets' if sys.platform.startswith('win') else '.secrets')
    return os.path.join(basedir, env_str)


# TODO(dittrich): Finish tests for groups

class Test_Groups(unittest.TestCase):
    @unittest.skip("Finish tests for groups")
    def test_skip_groups(self):
        pass


if __name__ == '__main__':
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
