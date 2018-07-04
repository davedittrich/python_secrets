#!/usr/bin/env python

"""
test_python_secrets.main
-------------------------

Tests for `python_secrets.main` module.
"""

import os
import unittest

from python_secrets.main import *

TEST_ENVIRONMENT = 'testenv'
TEST_SECRETS_FILE = 'testfile.yml'


class Test_MainFunctions(unittest.TestCase):

    def setUp(self):
        os.environ['D2_ENVIRONMENT'] = TEST_ENVIRONMENT
        os.environ['D2_SECRETS_FILE'] = TEST_SECRETS_FILE

    def tearDown(self):
        pass

    def test_default_environment(self):
        assert default_environment() == TEST_ENVIRONMENT

    def test_default_secrets_file_name(self):
        assert default_secrets_file_name() == TEST_SECRETS_FILE

    def test_default_secrets_dir(self):
        if os.sep == "\\":
            assert default_secrets_dir() == '{}\\secrets\\{}'.format(
                os.environ.get('USERPROFILE'),
                os.environ.get('D2_ENVIRONMENT'))
        elif os.sep == '/':
            assert default_secrets_dir() == '{}/.secrets/{}'.format(
                os.environ.get('HOME'),
                os.environ.get('D2_ENVIRONMENT'))
        else:
            return False

    def test_default_deployment_secrets_dir(self):
        assert default_deployment_secrets_dir() == os.path.join(
            default_secrets_dir(),
            default_secrets_file_name().replace('.yml', '.d'))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
