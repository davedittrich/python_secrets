# Generic modular configuration file manager.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://pypi.python.org/pypi/python_secrets

"""Python secrets management app"""

# Standard library modules.
import collections
import logging
import os
import posixpath
import sys
import yaml
import yamlreader

from . import __version__

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager
from numpy import random


# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG=False
ENVIRONMENT = os.getenv('D2_ENVIRONMENT', None)
SECRETS_FILE_NAME = os.getenv('D2_SECRETS_FILE', 'secrets.yml')
SECRETS_DIR = os.getenv(
            'D2_SECRETS_DIR',
            '.' if not ENVIRONMENT else '{}/.secrets'.format(os.environ.get('HOME'))
        )
DEPLOYMENT_SECRETS_DIR = posixpath.join(SECRETS_DIR, ENVIRONMENT).replace("\\", "/") if ENVIRONMENT else SECRETS_DIR
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
        self.secrets_changed = False

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
        self.read_secrets_descriptions()
        self.read_secrets()

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)
            self.LOG.info('not writing secrets out due to error')
        else:
            if self.secrets_changed:
                self.write_secrets()

    def set_environment(self, environment=ENVIRONMENT):
        """Set variable for current environment"""
        self.environment = environment

    def get_environment(self):
        """Get the current environment setting"""
        return self.environment

    def set_secrets_dir(self, secrets_dir=SECRETS_DIR, environment=ENVIRONMENT):
        """Set variable for current secrets directory"""
        if not environment:
            self.secrets_dir = secrets_dir
        else:
            self.secrets_dir = posixpath.join(secrets_dir, environment)

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

    def get_secrets_descriptions_dir(self):
        """Get the current secrets descriptions directory setting"""
        # environment_dir = posixpath.join(self.get_secrets_dir(), self.get_environment())
        return '{}.d'.format(os.path.splitext(self.get_secrets_file_path())[0])

    def set_redact(self, redact=True):
        """Set redaction flag"""
        assert type(redact) is bool, "set_redact(): redact must be bool"
        self.redact = redact

    def get_redact(self):
        """Get redaction flag"""
        return self.redact

    def get_secret(self, secret):
        """Get the value of secret

        :param secret: :type: string
        :return: value of secret
        """
        return self.secrets[secret]

    def set_secret(self, secret, value):
        """Set secret to value

        :param secret: :type: string
        :param value: :type: string
        :return:
        """
        self.secrets[secret] = value
        self.secrets_changed = True

    def read_secrets(self):
        """Load the current secrets from .yml file"""
        self.secrets = collections.OrderedDict()
        self.LOG.debug('reading secrets from {}'.format(
            self.get_secrets_file_path()))
        with open(self.get_secrets_file_path(), 'r') as f:
            self.secrets = yaml.load(f)
            # except Exception as e:

    def write_secrets(self):
        """Write out the current secrets for use by Ansible, only if any changes were made"""
        if self.secrets_changed:
            self.LOG.debug('writing secrets to {}'.format(
                self.get_secrets_file_path()))
            with open(self.get_secrets_file_path(), 'w') as outfile:
                yaml.dump(self.secrets,
                          outfile,
                          encoding=('utf-8'),
                          explicit_start=True,
                          default_flow_style=False
                          )
        else:
            self.LOG.debug('not writing secrets (unchanged)')

    def read_secrets_descriptions(self):
        """Load the descriptions of groups of secrets from a .d directory"""
        self.secrets_descriptions = collections.OrderedDict()
        groups_dir = self.get_secrets_descriptions_dir()
        if os.path.exists(groups_dir):
            self.LOG.debug('reading secrets descriptions from {}'.format(
                self.get_secrets_descriptions_dir()))
            try:
                self.secrets_descriptions = yamlreader.yaml_load(
                    groups_dir + '/*.yml'
                )
            except YAMLReaderError as e:
                self.LOG.info('no secrets descriptions files found')
        else:
            self.LOG.info('secrets descriptions directory not found')

def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``python_secrets`` program.
    """

    myapp = PythonSecretsApp()
    return myapp.run(argv)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# EOF
