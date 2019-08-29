#!/usr/bin/env python

"""
test_psec.utils
---------------

Tests for `psec.utils` module.
"""

import unittest

import psec.utils

class Test_Utils(unittest.TestCase):

    def setUp(self):
        self.lst = [
               {'Variable': 'jenkins_admin_password', 'Type': 'password'},
               {'Variable': 'ca_rootca_password', 'Type': 'password'},
               ]

    def tearDown(self):
        pass

    def test_redact_false(self):
        assert psec.utils.redact("foo", False) == "foo"

    def test_redact_true(self):
        assert psec.utils.redact("foo", True) == "REDACTED"

    def test_find_present(self):
        assert psec.utils.find(self.lst,
                               'Variable',
                               'ca_rootca_password') == 1

    def test_find_absent(self):
        assert psec.utils.find(self.lst,
                               'Variable',
                               'something_not_there') is None


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
