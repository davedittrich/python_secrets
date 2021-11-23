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
import os
import sys
import textwrap
import time
import webbrowser

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager
from psec import __version__
from psec.secrets_environment import (
    get_default_environment,
    SecretsEnvironment,
)
from psec.utils import (
    bell,
    show_current_value,
    umask,
    DEFAULT_UMASK,
    Timer,
)

if sys.version_info < (3, 6, 0):
    print((f"[-] The {os.path.basename(sys.argv[0])} "
           "requires Python 3.6.0 or newer\n"
           f"[-] Found Python {sys.version}"),
          file=sys.stderr)
    sys.exit(1)


# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG = False


class PythonSecretsApp(App):
    """Python secrets application class."""

    def __init__(self):
        super().__init__(
            description=__doc__.strip(),
            version=__version__,
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
        # Alias the following variable for consistency using code
        # using "logger" instead of "LOG".
        self.logger = self.LOG

    def build_option_parser(self, description, version):
        parser = super(PythonSecretsApp, self).build_option_parser(
            description,
            version
        )
        # OCD hack: Make ``help`` output report main program name,
        # even if run as ``python -m psec.main`` or such.
        if parser.prog.endswith('.py'):
            parser.prog = self.command_manager.namespace
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
        default_env = get_default_environment()
        parser.add_argument(
            '-e', '--environment',
            metavar='<environment>',
            dest='environment',
            default=default_env,
            help="Deployment environment selector " +
                 "(Env: D2_ENVIRONMENT; default: {})".format(
                    default_env
                    )
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
            '--preserve-existing',
            action='store_true',
            dest='preserve_existing',
            default=False,
            help=("Don't allow over-writing existing environment variables "
                  "(default: False)")
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
        parser.add_argument(
            '--rtd',
            action='store_true',
            dest='rtd',
            default=False,
            help=('Open ReadTheDocs documentation on '
                  '"help" command (default: False)')
        )
        parser.epilog = textwrap.dedent(f"""\
            For programs that inherit values through environment variables, you can
            export secrets using the ``-E`` option to the ``run`` subcommand, e.g.
            ``psec -E run -- terraform plan -out=$(psec environments path --tmpdir)/tfplan``
            The environment variable ``PYTHON_SECRETS_ENVIRONMENT`` will also be exported
            with the identifier of the associated source environment.

            To improve overall security when doing this, a default process umask of
            {DEFAULT_UMASK:#05o} is set when the app initializes. When running programs like the
            example above where they create sensitive files in the environment
            directory, this reduces the chance that secrets created during execution
            will end up with overly broad permissions.  If you need to relax these
            permissions, use the ``--umask`` option to apply the desired mask.

            To control the browser that is used with the ``help --rtd`` command,
            set the BROWSER environment variable (e.g., ``BROWSER=lynx``).
            See: https://github.com/python/cpython/blob/3.8/Lib/webbrowser.py

            Current working dir: {os.getcwd()}
            Python interpreter:  {sys.executable} (v{sys.version.split()[0]})
            Environment variables consumed:
              BROWSER             Default browser for use by webbrowser.open().{show_current_value('BROWSER')}
              D2_ENVIRONMENT      Default environment identifier.{show_current_value('D2_ENVIRONMENT')}
              D2_SECRETS_BASEDIR  Default base directory for storing secrets.{show_current_value('D2_SECRETS_BASEDIR')}
              D2_SECRETS_BASENAME Default base name for secrets storage files.{show_current_value('D2_SECRETS_BASENAME')}
              D2_NO_REDACT        Default redaction setting for ``secrets show`` command.{show_current_value('D2_NO_REDACT')}
            """)  # noqa

        return parser

    def initialize_app(self, argv):
        self.logger.debug('[*] initialize_app(%s)', str(self.__class__))
        if sys.version_info <= (3, 6):
            raise RuntimeError('This program uses the Python "secrets" ' +
                               'module, which requires Python 3.6 or higher')

    def prepare_to_run_command(self, cmd):
        self.logger.debug("[*] prepare_to_run_command('%s')", cmd.cmd_name)
        #
        # Process ReadTheDocs web browser request here and then
        # fall through, which also produces help output on the
        # command line. The webbrowser module doesn't seem to work
        # consistently on Ubuntu Linux, so this helps a little
        # though may be confusing when you don't get a browser opening
        # up like you expect.
        rtd_url = 'https://python-secrets.readthedocs.io/en/latest/usage.html'
        if cmd.cmd_name == 'help' and self.options.rtd:
            for line in [
                '[+] Opening online documentation for python_secrets on ReadTheDocs.',  # noqa
                '[+] If a browser does not open, make sure that you are online and/or',  # noqa
                '[+] enter the following URL in your chosen browser:',
                rtd_url,
            ]:
                self.logger.info(line)
            print('\n\n')
            bell()
            time.sleep(3)
            # TODO(dittrich): Add more specificity
            # FYI, new= is ignored on Windows per:
            # https://stackoverflow.com/questions/1997327/python-webbrowser-open-setting-new-0-to-open-in-the-same-browser-window-does  # noqa

            webbrowser.open(rtd_url, new=0, autoraise=True)
        self.timer.start()
        os.umask(self.options.umask)
        self.logger.debug("[+] using environment '%s'",
                          self.options.environment)
        self.environment = self.options.environment
        self.secrets_basedir = self.options.secrets_basedir
        # Don't output error messages when "complete" command used
        if cmd.cmd_name != 'complete':
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
                preserve_existing=self.options.preserve_existing,
                verbose_level=self.options.verbose_level,
                env_var_prefix=self.options.env_var_prefix,
                )

    def clean_up(self, cmd, result, err):
        self.logger.debug("[-] clean_up command '%s'", cmd.cmd_name)
        if err:
            self.logger.debug("[-] got an error: %s", str(err))
            if self.secrets is not None and self.secrets.changed():
                self.logger.info('[-] not writing secrets out due to error')
        elif cmd.cmd_name not in ['help', 'complete']:
            if self.secrets.changed():
                self.secrets.write_secrets()
            if (self.options.elapsed or
                    (self.options.verbose_level > 1
                     and cmd.cmd_name != "complete")):
                self.timer.stop()
                elapsed = self.timer.elapsed()
                self.stderr.write('[+] elapsed time {}\n'.format(elapsed))
                bell()


def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``psec`` program.
    """

    myapp = PythonSecretsApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
