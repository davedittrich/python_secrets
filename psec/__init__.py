# -*- coding: utf-8 -*-

from importlib.metadata import (
    version,
    PackageNotFoundError,
)

from psec._version import (
    __version__,
    __version_tuple__,
)

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'
__release__ = '24.10.7'

if __version__ in ['0.0.0', '0.1.0']:
    try:
        __version__ = version("python-secrets")
    except PackageNotFoundError:
        __version__ = __release__

__all__ = [
    '__author__',
    '__email__',
    '__release__',
    '__version__',
    '__version_tuple__',
]

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
