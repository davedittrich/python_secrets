# -*- coding: utf-8 -*-

import os
import pathlib
import pbr.version

# PBR has a bug that produces incorrect version numbers
# if you run ``psec --version`` in another Git repo.
# This attempted workaround only uses PBR for getting
# version and revision number if run in a directory
# path that contains strings that appear to be
# a python_secrets repo clone.

p = pathlib.Path(os.getcwd())
if 'python_secrets' in p.parts or 'psec' in p.parts:
    try:
        version_info = pbr.version.VersionInfo('psec')
        __version__ = version_info.cached_version_string()
        __release__ = version_info.release_string()
    except Exception:
        pass
else:
    __version__ = '21.2.0'
    __release__ = __version__

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'

__all__ = ['__author__', '__email__', '__version__', '__release__']

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
