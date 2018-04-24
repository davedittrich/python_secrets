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
        pass

    def tearDown(self):
        pass

    def test_000_redact(self):
        assert redact("foo", False) == "foo"

    def test_001_redact(self):
        assert redact("foo", True) == "REDACTED"


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
