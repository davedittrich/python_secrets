#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python_secrets.utils
-------------------------

Tests for `python_secrets.utils` module.
"""

import unittest

from python_secrets.utils import *

class Test_Utils(unittest.TestCase):

    def setUp(self):
        self.lst = [
               {'Variable': 'jenkins_admin_password', 'Type': 'password'},
               {'Variable': 'ca_rootca_password', 'Type': 'password'},
               ]

    def tearDown(self):
        pass

    def test_000_redact(self):
        assert redact("foo", False) == "foo"

    def test_001_redact(self):
        assert redact("foo", True) == "REDACTED"

    def test_002_find(self):
        assert find(self.lst, 'Variable', 'ca_rootca_password') == 1

    def test_003_find(self):
        assert find(self.lst, 'Variable', 'something_not_there') is None


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
