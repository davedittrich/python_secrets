#!/usr/bin/env python

"""
test_python_secrets.main
-------------------------

Tests for `python_secrets.main` module.
"""

import os
import unittest

from python_secrets.main import *

class Test_MainFunctions(unittest.TestCase):

    def setUp(self):
        os.environ['D2_ENVIRONMENT'] = 'unittest'
        os.environ['D2_SECRETS_FILE'] = 'unittest.yml'

    def tearDown(self):
        pass

    def test_default_environment(self):
        assert default_environment() == 'unittest'

    def test_default_secrets_file_name(self):
        assert default_secrets_file_name() == 'unittest.yml'

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
        pass


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
