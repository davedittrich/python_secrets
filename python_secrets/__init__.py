import pbr.version

version_info = pbr.version.VersionInfo('python_secrets')
try:
    __version__ = version_info.version_string()
except AttributeError:
    __version__ = '18.11.5'

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'

__all__ = ['__author__', '__email__', '__version__']

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
