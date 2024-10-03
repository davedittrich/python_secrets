# -*- coding: utf-8 -*-

"""
Modular secrets and settings management app.

Generic modular configuration file manager.

"""

# Standard imports
import sys

# Local imports
from psec import __version__
from psec.app import PythonSecretsApp

# Register handlers to ensure parser arguments are available.
from psec.secrets_environment.handlers import *  # noqa  pylint: disable=wildcard-import, unused-wildcard-import


def main(argv=None):
    """
    Command line interface for the ``psec`` program.
    """
    if argv is None:
        argv = sys.argv[1:]
    myapp = PythonSecretsApp(
        namespace='psec',
        docs_url='https://python-secrets.readthedocs.io/en/latest/usage.html',
        version=__version__,
    )
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
