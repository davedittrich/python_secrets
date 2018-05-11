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

from . import __version__
from .utils import find

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager


# Use syslog for logging?
# TODO(dittrich) Make this configurable, since it can fail on Mac OS X
SYSLOG = False

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def default_environment():
    """Return environment identifier"""
    return os.getenv('D2_ENVIRONMENT', None)


def default_secrets_file_name():
    """Return just the file name for secrets file"""
    return os.getenv('D2_SECRETS_FILE', 'secrets.yml')


def default_secrets_dir():
    """Return the directory path root for secrets storage"""
    return os.getenv(
            'D2_SECRETS_DIR',
            '.' if not default_environment()
            else '{}/.secrets/{}'.format(
                os.environ.get('HOME'),
                default_environment())
        )


def default_deployment_secrets_dir():
    """Return the"""
    _env = default_environment()
    return posixpath.join(
        default_secrets_dir(),
        _env
    ).replace("\\", "/") if _env else default_secrets_dir()  # noqa


def default_secrets_file_path():
    """Return full path to secrets file"""
    return posixpath.join(
        default_deployment_secrets_dir(),
        default_secrets_file_name()
    )


def default_program():
    """Return program name"""
    return os.path.basename(os.path.dirname(__file__))


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
        self.secrets_descriptions = collections.OrderedDict()
        self.secrets = collections.OrderedDict()
        self.secrets_changed = False
        self.groups = None

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
            default=default_environment(),
            help="Deployment environment selector " +
                 "(Env: D2_ENVIRONMENT; default: {})".format(
                     default_environment())
        )
        parser.add_argument(
            '-d', '--secrets-dir',
            metavar='<secrets-directory>',
            dest='secrets_dir',
            default=default_secrets_dir(),
            help="Root directory for holding secrets " +
                 "(Env: D2_SECRETS_DIR; default: {})".format(
                     default_secrets_dir())
        )
        parser.add_argument(
            '-s', '--secrets-file',
            metavar='<secrets-file>',
            dest='secrets_file',
            default=default_secrets_file_name(),
            help="Secrets file (default: {})".format(
                default_secrets_file_name())
        )
        return parser

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')
        self.set_environment(self.options.environment)
        self.set_secrets_dir(self.options.secrets_dir)
        self.set_secrets_file(self.options.secrets_file)

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)
        if not self.options.deferred_help:
            self.read_secrets_descriptions()
            self.read_secrets()

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)
            if self.secrets_changed:
                self.LOG.info('not writing secrets out due to error')
        else:
            if self.secrets_changed:
                self.write_secrets()

    def set_environment(self, environment=default_environment()):
        """Set variable for current environment"""
        self.environment = environment

    def get_environment(self):
        """Get the current environment setting"""
        return self.environment

    def set_secrets_dir(self,
                        secrets_dir=default_secrets_dir(),
                        environment=default_environment()):
        """Set variable for current secrets directory"""
        if not environment:
            self.secrets_dir = secrets_dir
        else:
            self.secrets_dir = posixpath.join(secrets_dir, environment)

    def get_secrets_dir(self):
        """Get the current secrets directory setting"""
        return self.secrets_dir

    def set_secrets_file(self,
                         secrets_file=default_secrets_file_path()):
        """Set variable with name of secrets file"""
        self.secrets_file = secrets_file

    def get_secrets_file(self):
        """Get name of secrets file"""
        return self.secrets_file

    def get_secrets_file_path(self):
        """Get absolute path to secrets file"""
        environment = self.get_environment()
        if not environment:
            return posixpath.join(self.secrets_dir, self.secrets_file)
        else:
            return posixpath.join(
                posixpath.join(self.secrets_dir, self.environment),
                self.secrets_file
            )

    def get_secrets_descriptions_dir(self):
        """Get the current secrets descriptions directory setting"""
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
        self.LOG.debug('reading secrets from {}'.format(
            self.get_secrets_file_path()))
        with open(self.get_secrets_file_path(), 'r') as f:
            self.secrets = yaml.safe_load(f)
            # except Exception as e:

    def write_secrets(self):
        """Write out the current secrets for use by Ansible,
        only if any changes were made"""
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
        groups_dir = self.get_secrets_descriptions_dir()
        # Ignore .order file and any other non-YAML file extensions
        extensions = ['yml', 'yaml']
        file_names = [fn for fn in os.listdir(groups_dir)
                      if any(fn.endswith(ext) for ext in extensions)]
        self.groups = [os.path.splitext(fn) for fn in file_names]
        if os.path.exists(groups_dir):
            self.LOG.debug('reading secrets descriptions from {}'.format(
                groups_dir))
            try:
                # Iterate over files in directory, loading them into
                # dictionaries as dictionary keyed on group name.
                for file in file_names:
                    group = os.path.splitext(file)[0]
                    with open(os.path.join(groups_dir, file), 'r') as f:
                        data = yaml.safe_load(f)
                    self.secrets_descriptions[group] = data
            except Exception:
                self.LOG.info('no secrets descriptions files found')
        else:
            self.LOG.info('secrets descriptions directory not found')

    def get_secret_type(self, variable):
        """Get the Type of variable from set of secrets descriptions"""
        for g in self.secrets_descriptions.keys():
            i = find(
                self.secrets_descriptions[g],
                'Variable',
                variable)
            if i is not None:
                try:
                    return self.secrets_descriptions[g][i]['Type']
                except KeyError:
                    return None
        return None

    # TODO(dittrich): Not very DRY (but no time now)
    def get_secret_arguments(self, variable):
        """Get the Arguments of variable from set of secrets descriptions"""
        for g in self.secrets_descriptions.keys():
            i = find(
                self.secrets_descriptions[g],
                'Variable',
                variable)
            if i is not None:
                try:
                    return self.secrets_descriptions[g][i]['Arguments']
                except KeyError:
                    return {}
        return {}

    def get_items_from_group(self, group):
        """Get the variables in a secrets description group"""
        return [i['Variable'] for i in self.secrets_descriptions[group]]

    def is_item_in_group(self, item, group):
        """Return true or false based on item being in group"""
        return find(
                self.secrets_descriptions[group],
                'Variable',
                item) is not None

    def get_groups(self):
        """Get the secrets description groups"""
        return [g for g in self.secrets_descriptions]


def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``python_secrets`` program.
    """

    myapp = PythonSecretsApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# EOF
