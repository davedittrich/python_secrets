#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python_secrets.main
------------------------

Tests for `python_secrets.main` module.
"""

import unittest
import os

from python_secrets.main import *

class Test_Main_1(unittest.TestCase):

    def setUp(self):
        self.home = os.environ['HOME']
        self.environment = os.getenv('D2_ENVIRONMENT', None)
        os.environ['D2_ENVIRONMENT'] = 'TESTING'
        self.environment = os.getenv('D2_SECRETS_FILE', None)
        os.environ['D2_SECRETS_FILE'] = 'testing.yml'

    def tearDown(self):
        if self.environment is not None:
            os.environ['D2_ENVIRONMENT'] = self.environment

    def test_default_environment_set(self):
        assert default_environment() == 'TESTING'

    def test_secrets_file_name_set(self):
        assert default_secrets_file_name() == 'testing.yml'

    def test_secrets_dir_set(self):
        _dirname = '{}/.secrets/{}'.format(
            self.home,
            default_environment())
        assert default_secrets_dir() == _dirname

    def test_default_deployment_secrets_dir(self):
        assert default_deployment_secrets_dir() == \
            posixpath.join(default_secrets_dir(), 'TESTING')


class Test_Main_2(unittest.TestCase):

    def setUp(self):
        self.environment = os.getenv('D2_ENVIRONMENT', None)
        if self.environment is not None:
            del os.environ['D2_ENVIRONMENT']
        self.secrets_file = os.getenv('D2_SECRETS_FILE', None)
        if self.secrets_file is not None:
            del os.environ['D2_SECRETS_FILE']

    def tearDown(self):
        if self.environment is not None:
            os.environ['D2_ENVIRONMENT'] = self.environment
        if self.secrets_file is not None:
            os.environ['D2_SECRETS_FILE'] = self.secrets_file

    def test_default_environment_unset(self):
        assert default_environment() is None

    def test_secrets_file_name_unset(self):
        assert default_secrets_file_name() == 'secrets.yml'

    def test_secrets_dir_unset(self):
        assert default_secrets_dir() == '.'

    def test_default_deployment_secrets_dir_unset(self):
        assert default_deployment_secrets_dir() == \
            default_secrets_dir()

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
