# -*- coding: utf-8 -*-

"""
Python secrets management app.

Generic modular configuration file manager.

"""

# Standard imports
import logging
import os
import sys
import textwrap
import time
import webbrowser

# External imports
from cliff.app import App
from cliff.commandmanager import CommandManager

# Local imports
from psec import __version__
from psec.secrets_environment import SecretsEnvironment
from psec.secrets_environment.factory import SecretFactory
from psec.utils import (  # noqa
    bell,
    ensure_secrets_basedir,
    get_default_environment,
    get_default_secrets_basedir,
    permissions_check,
    show_current_value,
    umask,
    DEFAULT_UMASK,
    Timer,
)

# Register handlers to ensure parser arguments are available.
from psec.secrets_environment.handlers import *  # noqa


# Commands that do not need secrets environments.
DOES_NOT_NEED_SECRETS = ['complete', 'help', 'init', 'utils']
# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG = False
D2_LOGFILE = os.getenv('D2_LOGFILE', None)

DEFAULT_ENVIRONMENT = get_default_environment()
DEFAULT_BASEDIR = get_default_secrets_basedir()


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
        self.secret_factory = SecretFactory()

    def build_option_parser(self, description, version):
        parser = super().build_option_parser(
            description,
            version
        )
        # OCD hack: Make ``help`` output report main program name,
        # even if run as ``python -m psec.main`` or such.
        if parser.prog.endswith('.py'):
            parser.prog = self.command_manager.namespace
        # Replace the cliff SmartHelpFormatter class before first use
        # by subcommand `--help`.
        # pylint: disable=wrong-import-order
        from psec.utils import CustomFormatter
        from cliff import _argparse
        _argparse.SmartHelpFormatter = CustomFormatter
        # pylint: enable=wrong-import-order
        # We also need to change app parser, which is separate.
        parser.formatter_class = CustomFormatter
        # Global options
        parser.add_argument(
            '--elapsed',
            action='store_true',
            dest='elapsed',
            default=False,
            help='Print elapsed time on exit'
        )
        parser.add_argument(
            '-d', '--secrets-basedir',
            metavar='<secrets-basedir>',
            dest='secrets_basedir',
            default=DEFAULT_BASEDIR,
            help='Root directory for holding secrets (Env: D2_SECRETS_BASEDIR)'
        )
        parser.add_argument(
            '-e', '--environment',
            metavar='<environment>',
            dest='environment',
            default=DEFAULT_ENVIRONMENT,
            help='Deployment environment selector (Env: D2_ENVIRONMENT)'
        )
        parser.add_argument(
            '-s', '--secrets-file',
            metavar='<secrets-file>',
            dest='secrets_file',
            default=None,
            help='Secrets file'
        )
        parser.add_argument(
            '-P', '--env-var-prefix',
            metavar='<prefix>',
            dest='env_var_prefix',
            default=None,
            help='Prefix string for environment variables'
        )
        parser.add_argument(
            '-E', '--export-env-vars',
            action='store_true',
            dest='export_env_vars',
            default=False,
            help='Export secrets as environment variables'
        )
        parser.add_argument(
            '--preserve-existing',
            action='store_true',
            dest='preserve_existing',
            default=False,
            help='Prevent over-writing existing environment variables'
        )
        parser.add_argument(
            '--init',
            action='store_true',
            dest='init',
            default=False,
            help='Ensure the directory for holding secrets is initialized'
        )
        parser.add_argument(
            '--umask',
            metavar='<umask>',
            type=umask,
            dest='umask',
            default=DEFAULT_UMASK,
            help='Permissions mask to apply during app execution'
        )
        parser.add_argument(
            '--rtd',
            action='store_true',
            dest='rtd',
            default=False,
            help='Open ReadTheDocs documentation on "help" command'
        )
        parser.epilog = textwrap.dedent(f"""
            For programs that inherit values through environment variables, you can export
            secrets using the ``-E`` option to the ``run`` subcommand, e.g.  ``psec -E run
            -- terraform plan -out=$(psec environments path --tmpdir)/tfplan`` The
            environment variable ``PYTHON_SECRETS_ENVIRONMENT`` will also be exported with
            the identifier of the associated source environment.

            To improve overall security, a default process umask of {DEFAULT_UMASK:#05o}
            is set when the app initializes. When running programs like the example above
            where files containing sensitive data are created in the environment
            directory, this reduces the chance that files created during execution will
            end up with overly broad permissions.  If you need to relax these permissions,
            use the ``--umask`` option to apply the desired mask.

            To control the browser that is used with the ``help --rtd`` command, set the
            BROWSER environment variable (e.g., ``BROWSER=lynx``).  See:
            https://github.com/python/cpython/blob/3.8/Lib/webbrowser.py

            Current working dir: {os.getcwd()}
            Python interpreter:  {sys.executable} (v{sys.version.split()[0]})

            Environment variables consumed:
              BROWSER             Default browser for use by webbrowser.open().{show_current_value('BROWSER')}
              D2_ENVIRONMENT      Default environment identifier.{show_current_value('D2_ENVIRONMENT')}
              D2_LOGFILE          Path to file for receiving log messages.{show_current_value('D2_LOGFILE')}
              D2_SECRETS_BASEDIR  Default base directory for storing secrets.{show_current_value('D2_SECRETS_BASEDIR')}
              D2_SECRETS_BASENAME Default base name for secrets storage files.{show_current_value('D2_SECRETS_BASENAME')}
              D2_NO_REDACT        Default redaction setting for ``secrets show`` command.{show_current_value('D2_NO_REDACT')}
            """)  # noqa
        return parser

    def initialize_app(self, argv):
        self.logger.debug('[*] initialize_app(%s)', self.__class__.NAME)
        if sys.version_info <= (3, 6):
            raise RuntimeError(
                'This program requires Python 3.6 or higher'
            )
        os.umask(self.options.umask)
        self.timer.start()

    def prepare_to_run_command(self, cmd):
        self.logger.debug("[*] prepare_to_run_command('%s')", cmd.cmd_name)
        #
        # Process ReadTheDocs web browser request here and then
        # fall through, which also produces help output on the
        # command line. The webbrowser module doesn't seem to work
        # consistently on Ubuntu Linux and some versions of Mac OS X (Darwin),
        # so this helps a little though may be confusing when you don't
        # get a browser opening up like you expect.
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
        self.logger.debug(
            "[+] using environment '%s'", self.options.environment
        )
        # Set up an environment for the app, making sure to export runtime
        # options matching those from the command line and environment
        # variables for subprocesses to inherit. It's OK to warn here about
        # missing base directory (which will happen on first use), but don't
        # force the program to exit when not necessary.
        #
        env_environment = os.environ.get('D2_ENVIRONMENT')
        self.environment = self.options.environment
        if (
            env_environment is None
            or env_environment != self.environment
        ):
            os.environ['D2_ENVIRONMENT'] = str(self.environment)
        env_secrets_basedir = os.environ.get('D2_SECRETS_BASEDIR')
        self.secrets_basedir = ensure_secrets_basedir(
            secrets_basedir=self.options.secrets_basedir,
            allow_create=(
                self.options.init
                or cmd.cmd_name.startswith('init')
            ),
            verbose_level=self.options.verbose_level,
        )
        if (
            env_secrets_basedir is None
            or env_secrets_basedir != str(self.secrets_basedir)
        ):
            os.environ['D2_SECRETS_BASEDIR'] = str(self.secrets_basedir)
        self.secrets_file = self.options.secrets_file
        cmd_base = cmd.cmd_name.split(' ')[0]
        if cmd_base not in DOES_NOT_NEED_SECRETS:
            self.secrets = SecretsEnvironment(
                environment=self.environment,
                create_root=False,
                secrets_basedir=self.secrets_basedir,
                secrets_file=self.secrets_file,
                export_env_vars=self.options.export_env_vars,
                preserve_existing=self.options.preserve_existing,
                verbose_level=self.options.verbose_level,
                env_var_prefix=self.options.env_var_prefix,
            )
            permissions_check(
                self.secrets_basedir,
                verbose_level=self.options.verbose_level,
            )
        self.logger.debug("[*] running command '%s'", cmd.cmd_name)

    def clean_up(self, cmd, result, err):
        self.logger.debug("[-] clean_up command '%s'", cmd.cmd_name)
        if err:
            self.logger.debug("[-] got an error: %s", str(err))
            if self.secrets is not None and self.secrets.changed():
                self.logger.info(
                    '[-] not writing changed secrets out due to error'
                )
            sys.exit(result)
        if self.secrets is not None and self.secrets.changed():
            self.secrets.write_secrets()
        if (
            self.options.elapsed
            or (
                self.options.verbose_level > 1
                and cmd.cmd_name != "complete"
            )
        ):
            self.timer.stop()
            elapsed = self.timer.elapsed()
            self.stderr.write('[+] elapsed time {}\n'.format(elapsed))
            bell()


def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``psec`` program.
    """
    if D2_LOGFILE is not None:
        logging.basicConfig(
            level=logging.INFO,
            filename=D2_LOGFILE,
            format="%(asctime)s.%(msecs).6d %(levelname)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    myapp = PythonSecretsApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
