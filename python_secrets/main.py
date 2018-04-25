# Generic modular configuration file manager.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://pypi.python.org/pypi/python_secrets

"""Python secrets management app"""

# Standard library modules.
import logging
import os
import posixpath
import sys

from . import __version__

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager


# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG=False
ENVIRONMENT = os.getenv('D2_ENVIRONMENT', '')
SECRETS_FILE_NAME = os.getenv('D2_SECRETS_FILE', 'secrets.yml')
SECRETS_DIR = os.getenv(
            'D2_SECRETS_DIR',
            '.' if ENVIRONMENT == '' else '{}/.secrets'.format(os.environ.get('HOME'))
        )
DEPLOYMENT_SECRETS_DIR = posixpath.join(SECRETS_DIR, ENVIRONMENT).replace("\\", "/")
SECRETS_FILE_PATH = posixpath.join(DEPLOYMENT_SECRETS_DIR, SECRETS_FILE_NAME)
PROGRAM = os.path.basename(os.path.dirname(__file__))
DESCRIPTION="""\n
\n
usage: {} <command> [<args>]\n
\n
Environment Variables:\n
D2_SECRETS_DIR   Root directory for storing secrets (e.g., "~/.secrets")\n
D2_ENVIRONMENT   Deployment environment (e.g., "do")\n"""

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

    def build_option_parser(self, description, version):
        parser = super(PythonSecretsApp, self).build_option_parser(
            description,
            version
        )
        # Global options
        parser.add_argument(
            '-e', '--environment',
            metavar='<environment>',
            dest='environment',
            default=ENVIRONMENT,
            help="Deployment environment selector "+
                 "(Env: D2_ENVIRONMENT; default: {})".format(ENVIRONMENT)
        )
        parser.add_argument(
            '-d', '--secrets-dir',
            metavar='<secrets-directory>',
            dest='secrets_dir',
            default=SECRETS_DIR,
            help="Root directory for holding secrets " +
                 "(Env: D2_SECRETS_DIR; default: {})".format(SECRETS_DIR)
        )
        parser.add_argument(
            '-s', '--secrets-file',
            metavar='<secrets-file>',
            dest='secrets_file',
            default=SECRETS_FILE_NAME,
            help="Secrets file (default: {})".format(SECRETS_FILE_NAME)
        )
        return parser

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')
        self.set_environment(self.options.environment)
        self.set_secrets_dir(self.options.secrets_dir)
        self.set_secrets_file(self.options.secrets_file)

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)

    def set_environment(self, environment=ENVIRONMENT):
        """Set variable for current environment"""
        self.environment = environment

    def get_environment(self):
        """Get the current environment setting"""
        return self.environment

    def set_secrets_dir(self, secrets_dir=SECRETS_DIR):
        """Set variable for current secrets directory"""
        self.secrets_dir = secrets_dir

    def get_secrets_dir(self):
        """Get the current secrets directory setting"""
        return self.secrets_dir

    def set_secrets_file(self, secrets_file=SECRETS_FILE_PATH):
        """Set variable with name of secrets file"""
        self.secrets_file = secrets_file

    def get_secrets_file(self):
        """Get name of secrets file"""
        return self.secrets_file

    def get_secrets_file_path(self):
        """Get absolute path to secrets file"""
        return posixpath.join(self.secrets_dir, self.secrets_file)

    def set_redact(self, redact=True):
        """Set redaction flag"""
        self.redact = redact

    def get_redact(self):
        """Get redaction flag"""
        return self.redact

def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``python_secrets`` program.
    """

    myapp = PythonSecretsApp()
    return myapp.run(argv)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# EOF
