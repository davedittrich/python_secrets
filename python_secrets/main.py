# Generic modular configuration file manager.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://pypi.python.org/pypi/python_secrets

"""Python secrets management app"""

# Standard library modules.
import logging
import os
import sys

from . import __version__
from python_secrets.secrets import SecretsEnvironment

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager


# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG = False

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def default_environment():
    """
    Returns the environment identifier specified by environment variable
    D2_ENVIRONMENT or None if not defined.
    """
    return os.getenv('D2_ENVIRONMENT', os.path.basename(os.getcwd()))


def default_secrets_basename():
    """Returns the file base name for secrets file"""
    return os.getenv('D2_SECRETS_BASENAME', 'secrets.yml')


def default_secrets_basedir(init=False):
    """
    Returns the directory path root for secrets storage and definitions.

    When more than one environment is being used, a single top-level
    directory in the user's home directory is the preferred location.
    This function checks to see if such a directory exists, and if
    so defaults to that location.

    If the environment variable "D2_SECRETS_BASEDIR" is set, that location
    is used instead.
    """

    _home = os.path.expanduser('~')
    _secrets_subdir = os.path.join(
        _home, "secrets" if '\\' in _home else ".secrets")
    _basedir = os.getenv(
            'D2_SECRETS_BASEDIR',
            _secrets_subdir)
    if not os.path.exists(_basedir) and init:
            os.mkdir(path=_basedir, mode=0o700)
    return _basedir


def default_secrets_descriptions_dir():
    """Return the path to the drop-in secrets description directory"""
    _env = default_environment()
    if not _env:
        return default_secrets_basedir()
    else:
        return os.path.join(default_secrets_basedir(),
                            default_secrets_basename().replace('.yml', '.d'))


def default_secrets_file_path():
    """Return full path to secrets file"""
    return os.path.join(
        default_secrets_basedir(),
        default_secrets_basename()
    )


class PythonSecretsApp(App):
    """Python secrets application class"""

    def __init__(self):
        super(PythonSecretsApp, self).__init__(
            description=__doc__.strip(),
            version=__version__,
            command_manager=CommandManager(
                namespace='python_secrets'
            ),
            deferred_help=True,
            )
        self.secrets = None

    def build_option_parser(self, description, version):
        parser = super(PythonSecretsApp, self).build_option_parser(
            description,
            version
        )
        # Global options
        parser.add_argument(
            '-d', '--secrets-basedir',
            metavar='<secrets-basedir>',
            dest='secrets_basedir',
            default=default_secrets_basedir(),
            help="Root directory for holding secrets " +
                 "(Env: D2_SECRETS_BASEDIR; default: {})".format(
                     default_secrets_basedir())
        )
        parser.add_argument(
            '-e', '--environment',
            metavar='<environment>',
            dest='environment',
            default=default_environment(),
            help="Deployment environment selector " +
                 "(Env: D2_ENVIRONMENT; default: {})".format(
                     default_environment())
        )
        parser.add_argument(
            '-s', '--secrets-file',
            metavar='<secrets-file>',
            dest='secrets_file',
            default=default_secrets_basename(),
            help="Secrets file (default: {})".format(
                default_secrets_basename())
        )
        parser.add_argument(
            '-P', '--env-var-prefix',
            metavar='<prefix>',
            dest='env_var_prefix',
            default=None,
            help="Prefix string for environment variables " +
                 "(default: None)"
        )
        parser.add_argument(
            '-E', '--export-env-vars',
            action='store_true',
            dest='export_env_vars',
            default=False,
            help="Export secrets as environment variables " +
                 "(default: False)"
        )
        parser.add_argument(
            '--init',
            action='store_true',
            dest='init',
            default=False,
            help="Initialize directory for holding secrets."
        )
        return parser

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')
        if sys.version_info <= (3, 6):
            raise RuntimeError('This program uses the Python "secrets" ' +
                               'module, which requires Python 3.6 or higher')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)
        self.secrets = SecretsEnvironment(
            environment=self.options.environment,
            secrets_root=self.options.secrets_basedir,
            secrets_file=self.options.secrets_file,
            export_env_vars=self.options.export_env_vars,
            env_var_prefix=self.options.env_var_prefix,
            )

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)
            if self.secrets.changed():
                self.LOG.info('not writing secrets out due to error')
        else:
            if self.secrets.changed():
                self.secrets.write_secrets()


def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``python_secrets`` program.
    """

    myapp = PythonSecretsApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
