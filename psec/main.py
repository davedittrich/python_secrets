# -*- coding: utf-8 -*-

"""
Python secrets management app

Generic modular configuration file manager.

Author: Dave Dittrich <dave.dittrich@gmail.com>
URL: https://pypi.python.org/pypi/python_secrets
"""

from __future__ import print_function

# Standard library modules.
import argparse
import logging
import os
import sys
import textwrap

from psec import __version__
from psec import __release__
from psec.secrets import SecretsEnvironment
from psec.utils import Timer

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

DEFAULT_UMASK = 0o077
MAX_UMASK = 0o777


def umask(value):
    if value.lower().find("o") < 0:
        raise argparse.ArgumentTypeError(
                'value ({}) must be expressed in ' +
                'octal form (e.g., "0o077")')
    ivalue = int(value, base=8)
    if ivalue < 0 or ivalue > MAX_UMASK:
        raise argparse.ArgumentTypeError(
                "value ({}) must be between 0 and " +
                "0o777".format(value))
    return ivalue


# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class PythonSecretsApp(App):
    """Python secrets application class"""

    def __init__(self):
        super(PythonSecretsApp, self).__init__(
            description=__doc__.strip(),
            version=__release__ if __release__ != __version__ else __version__,
            command_manager=CommandManager(
                namespace='psec'
            ),
            deferred_help=True,
            )
        self.secrets = None
        self.environment = None
        self.secrets_basedir = None
        self.secrets_file = None
        self.timer = Timer()

    def build_option_parser(self, description, version):
        parser = super(PythonSecretsApp, self).build_option_parser(
            description,
            version
        )
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Global options
        parser.add_argument(
            '--elapsed',
            action='store_true',
            dest='elapsed',
            default=False,
            help='Print elapsed time on exit (default: False)'
        )
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
        parser.add_argument(
            '--umask',
            metavar='<umask>',
            type=umask,
            dest='umask',
            default=DEFAULT_UMASK,
            help="Mask to apply during app execution " +
                 "(default: {:#05o})".format(DEFAULT_UMASK)
        )
        parser.epilog = textwrap.dedent("""\
            For programs that inherit values through environment variables, you can
            export secrets using the ``-E`` option to the ``run`` subcommand, e.g.
            ``psec -E run -- terraform plan -out=$(psec environments path --tmpdir)/tfplan``

            To improve overall security when doing this, a default process umask of
            {:#05o} is set when the app initializes. When running programs like the
            example above where they create sensitive files in the environment
            directory, this reduces the chance that secrets created during execution
            will end up with overly broad permissions.  If you need to relax these
            permissions, use the ``--umask`` option to apply the desired mask.
            """.format(DEFAULT_UMASK))  # noqa

        return parser

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')
        if sys.version_info <= (3, 6):
            raise RuntimeError('This program uses the Python "secrets" ' +
                               'module, which requires Python 3.6 or higher')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)
        self.timer.start()
        os.umask(self.options.umask)
        self.LOG.debug('using environment "{}"'.format(
            self.options.environment))
        self.environment = self.options.environment
        self.secrets_basedir = self.options.secrets_basedir
        # Don't output error messages when "complete" command used
        if cmd.__class__.__name__ != 'CompleteCommand':
            SecretsEnvironment.permissions_check(
                self.secrets_basedir,
                verbose_level=self.options.verbose_level,
                )
            self.secrets_file = self.options.secrets_file
            self.secrets = SecretsEnvironment(
                environment=self.environment,
                secrets_basedir=self.secrets_basedir,
                secrets_file=self.secrets_file,
                export_env_vars=self.options.export_env_vars,
                verbose_level=self.options.verbose_level,
                env_var_prefix=self.options.env_var_prefix,
                )

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)
            if self.secrets.changed():
                self.LOG.info('not writing secrets out due to error')
        elif cmd.__class__.__name__ != 'CompleteCommand':
            if self.secrets.changed():
                self.secrets.write_secrets()
            if (self.options.elapsed or
                    (self.options.verbose_level > 1
                     and cmd.__class__.__name__ != "CompleteCommand")):
                self.timer.stop()
                elapsed = self.timer.elapsed()
                self.stdout.write('[+] Elapsed time {}\n'.format(elapsed))
                if sys.stdout.isatty():
                    sys.stdout.write('\a')
                    sys.stdout.flush()


def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``psec`` program.
    """

    myapp = PythonSecretsApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
