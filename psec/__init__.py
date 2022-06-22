# -*- coding: utf-8 -*-

__version__ = None
__release__ = '22.6.1'

# Get development version from repository tags.
try:
    from setuptools_scm import get_version
    __version__ = get_version(root='..', relative_to=__file__)
except (ImportError, LookupError):
    pass

if __version__ is None:
    from pkg_resources import get_distribution, DistributionNotFound
    try:
        __version__ = get_distribution("psec").version
    except DistributionNotFound:
        pass

if __version__ is None:
    __version__ = __release__

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'

__all__ = ['__author__', '__email__', '__version__', '__release__']

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
