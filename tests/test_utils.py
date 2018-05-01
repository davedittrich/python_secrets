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

    def test_redact_false(self):
        assert redact("foo", False) == "foo"

    def test_redact_true(self):
        assert redact("foo", True) == "REDACTED"

    def test_find_present(self):
        assert find(self.lst, 'Variable', 'ca_rootca_password') == 1

    def test_find_absent(self):
        assert find(self.lst, 'Variable', 'something_not_there') is None


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
