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
        self.HOME = os.environ['HOME']
        self.ENVIRONMENT = os.getenv('D2_ENVIRONMENT', None)
        os.environ['D2_ENVIRONMENT'] = 'TESTING'
        self.BASEDIR = os.getenv('D2_SECRETS_BASEDIR', None)
        os.environ['D2_SECRETS_BASEDIR'] = '.'
        self.BASENAME = os.getenv('D2_SECRETS_BASENAME', None)
        os.environ['D2_SECRETS_BASENAME'] = 'testing.yml'

    def tearDown(self):
        if self.ENVIRONMENT is not None:
            os.environ['D2_ENVIRONMENT'] = self.ENVIRONMENT
        if self.BASEDIR is not None:
            os.environ['D2_SECRETS_BASEDIR'] = self.BASEDIR
        if self.BASENAME is not None:
            os.environ['D2_SECRETS_BASENAME'] = self.BASENAME

    def test_default_environment_set(self):
        self.assertEqual(default_environment(), 'TESTING')

    def test_secrets_basedir_set(self):
        self.assertEqual(default_secrets_basedir(), '.')

    def test_secrets_basename_set(self):
        self.assertEqual(default_secrets_basename(), 'testing.yml')

    def test_default_secrets_descriptions_dir(self):
        self.assertEqual(default_secrets_descriptions_dir(),
                         os.path.join(default_secrets_basedir(), 'testing.d'))


class Test_Main_2(unittest.TestCase):

    def setUp(self):
        self.ENVIRONMENT = os.getenv('D2_ENVIRONMENT', None)
        if self.ENVIRONMENT is not None:
            del os.environ['D2_ENVIRONMENT']
        self.BASEDIR = os.getenv('D2_SECRETS_BASEDIR', None)
        if self.BASEDIR is not None:
            del os.environ['D2_SECRETS_BASEDIR']
        self.BASENAME = os.getenv('D2_SECRETS_BASENAME', None)
        if self.BASENAME is not None:
            del os.environ['D2_SECRETS_BASENAME']

    def tearDown(self):
        if self.ENVIRONMENT is not None:
            os.environ['D2_ENVIRONMENT'] = self.ENVIRONMENT
        if self.BASENAME is not None:
            os.environ['D2_SECRETS_BASENAME'] = self.BASENAME
        if self.BASENAME is not None:
            os.environ['D2_SECRETS_BASENAME'] = self.BASENAME

    def test_default_environment_unset(self):
        _cwd = os.path.basename(os.getcwd())
        self.assertEqual(default_environment(), _cwd)

    def test_secrets_basename_unset(self):
        self.assertEqual(default_secrets_basename(), 'secrets.yml')

    def test_secrets_basedir_unset(self):
        self.assertEqual(default_secrets_basedir(),
                         os.path.join(os.path.expanduser('~'),
                                      '.secrets'))

    def test_default_deployment_secrets_dir_unset(self):
        _home = os.path.expanduser('~')
        _secrets_subdir = os.path.join(
            _home, "secrets" if '\\' in _home else ".secrets")
        self.assertEqual(default_secrets_basedir(),
                         _secrets_subdir)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
