#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python_secrets.secrets
---------------------------

Tests for `python_secrets.secrets` module.
"""

import unittest
import os

from python_secrets.secrets import SecretsEnvironment


class Test_SecretsEnvironment(unittest.TestCase):

    def setUp(self):
        self.ENVIRONMENT = os.getenv('D2_ENVIRONMENT', None)
        os.environ['D2_ENVIRONMENT'] = 'TESTING'
        self.cwd = os.getcwd()
        self.host = "example.com"
        self.homedir = os.path.expanduser('~')
        self.secrets_dir = os.path.join(
            self.homedir,
            "secrets" if '\\' in self.homedir else ".secrets")
        self.environment_dir = os.path.join(self.secrets_dir,
                                            os.path.basename(self.cwd))
        self.keys_dir = os.path.join(self.environment_dir, "keys")
        self.keys_host_dir = os.path.join(self.keys_dir, self.host)
        self.e = SecretsEnvironment(cwd=self.cwd)

    def tearDown(self):
        if self.ENVIRONMENT is not None:
            os.environ['D2_ENVIRONMENT'] = self.ENVIRONMENT

    def test_environment_path(self):
        self.assertEqual(self.e.environment_path(),
                         self.environment_dir)

    def test_environment_path_subdir(self):
        self.assertEqual(self.e.environment_path(subdir="keys"),
                         self.keys_dir)

    def test_environment_path_subdir_host(self):
        self.assertEqual(self.e.environment_path(subdir="keys",
                                                 host=self.host),
                         self.keys_host_dir)

    def test_environment_path_nosubdir_host(self):
        self.assertRaises(RuntimeError,
                          self.e.environment_path,
                          host=self.host)

    def test_environment_path_subdir_leadingslash(self):
        self.assertRaises(RuntimeError, self.e.environment_path, subdir="/keys")

    def test_environment_path_subdir_trailingslash(self):
        self.assertRaises(RuntimeError, self.e.environment_path, subdir="keys/")


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
