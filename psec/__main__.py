# -*- coding: utf-8 -*-

# Generic modular configuration file manager.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://pypi.python.org/pypi/python_secrets

# Make this module work with "python -m"

import sys
from psec.main import main

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
