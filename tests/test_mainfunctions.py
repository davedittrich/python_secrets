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
TEST_SECRETS_BASENAME = 'testfile.yml'


class Test_MainFunctions(unittest.TestCase):

    def setUp(self):
        os.environ['D2_ENVIRONMENT'] = TEST_ENVIRONMENT
        os.environ['D2_SECRETS_BASENAME'] = TEST_SECRETS_BASENAME

    def tearDown(self):
        pass

    def test_default_environment(self):
        self.assertEqual(default_environment(), TEST_ENVIRONMENT)

    def test_default_secrets_file_name(self):
        self.assertEqual(default_secrets_basename(), TEST_SECRETS_BASENAME)

    def test_default_secrets_basedir(self):
        if os.sep == "\\":
            self.assertEqual(default_secrets_basedir(),
                             '{}\\secrets'.format(
                                 os.environ.get('USERPROFILE')))
        elif os.sep == '/':
            self.assertEqual(default_secrets_basedir(),
                             '{}/.secrets'.format(
                                 os.environ.get('HOME')))
        else:
            return False

    def test_default_secrets_descriptions_dir(self):
        self.assertEqual(default_secrets_descriptions_dir(),
                         os.path.join(
                             default_secrets_basedir(),
                             default_secrets_basename().replace('.yml', '.d')))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
