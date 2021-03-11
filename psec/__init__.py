# -*- coding: utf-8 -*-

__version__, __release__ = None, None

try:
    from setuptools_scm import get_version
    __version__ = get_version(root='..', relative_to=__file__)
    __release__ = __version__.split('+')[0]
except (LookupError, ModuleNotFoundError):
    pass

if __version__ is None:
    from pkg_resources import get_distribution, DistributionNotFound
    try:
        __version__ = get_distribution("lim-cli").version
        __release__ = __version__
    except (DistributionNotFound, ModuleNotFoundError):
        pass

if __version__ is None:
    __version__ = '21.2.0'
    __release__ = __version__

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'

__all__ = ['__author__', '__email__', '__version__', '__release__']

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
