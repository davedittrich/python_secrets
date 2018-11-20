# Generic modular configuration file manager.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://pypi.python.org/pypi/python_secrets

"""Python secrets management app"""

from __future__ import print_function

# Standard library modules.
import logging
import os
import sys

from python_secrets import __version__
from python_secrets.secrets import SecretsEnvironment

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager

if sys.version_info < (3, 6, 0):
    print("The {} program ".format(os.path.basename(sys.argv[0])) +
          "prequires Python 3.6.0 or newer\n" +
          "Found Python {}".format(sys.version), file=sys.stderr)
    sys.exit(1)


# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG = False

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


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
        self.environment = None
        self.secrets_basedir = None
        self.secrets_file = None

    def build_option_parser(self, description, version):
        parser = super(PythonSecretsApp, self).build_option_parser(
            description,
            version
        )
        # Global options
        _env = SecretsEnvironment()
        parser.add_argument(
            '-d', '--secrets-basedir',
            metavar='<secrets-basedir>',
            dest='secrets_basedir',
            default=_env.secrets_basedir(),
            help="Root directory for holding secrets " +
                 "(Env: D2_SECRETS_BASEDIR; default: {})".format(
                     _env.secrets_basedir())
        )
        parser.add_argument(
            '-e', '--environment',
            metavar='<environment>',
            dest='environment',
            default=_env.environment(),
            help="Deployment environment selector " +
                 "(Env: D2_ENVIRONMENT; default: {})".format(
                     _env.environment())
        )
        parser.add_argument(
            '-s', '--secrets-file',
            metavar='<secrets-file>',
            dest='secrets_file',
            default=_env.secrets_basename(),
            help="Secrets file (default: {})".format(
                _env.secrets_basename())
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
        self.LOG.debug('using environment "{}"'.format(
            self.options.environment))
        self.environment = self.options.environment
        self.secrets_basedir = self.options.secrets_basedir
        self.secrets_file = self.options.secrets_file
        self.secrets = SecretsEnvironment(
            environment=self.environment,
            secrets_basedir=self.secrets_basedir,
            secrets_file=self.secrets_file,
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
