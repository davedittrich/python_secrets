import logging
import os
import textwrap

from cliff.command import Command
from cliff.lister import Lister
from python_secrets.secrets import is_valid_environment
from python_secrets.secrets import SecretsEnvironment
from python_secrets.utils import tree
from stat import S_IMODE


def _is_default(a, b):
    """
    Return "Yes" or "No" depending on whether e is the default
    environment or not.
    """
    return "Yes" if a == b else "No"


class EnvironmentsList(Lister):
    """List the current environments"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsList, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('listing environment(s)')
        default_environment = SecretsEnvironment().environment()
        columns = (['Environment', 'Default'])
        basedir = self.app.secrets.secrets_basedir()
        data = (
            [(e, _is_default(e, default_environment))
                for e in os.listdir(basedir)
                if is_valid_environment(
                    os.path.join(basedir, e),
                    self.app_args.verbose_level)]
        )
        return columns, data


class EnvironmentsCreate(Command):
    """Create environment(s)"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsCreate, self).get_parser(prog_name)
        parser.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Environment directory to clone from (default: None)"
        )
        parser.add_argument('args',
                            nargs='*',
                            default=[SecretsEnvironment().environment()])
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating environment(s)')
        # basedir = self.app.get_secrets_basedir()
        if len(parsed_args.args) == 0:
            parsed_args.args = list(self.app.environment)
        for e in parsed_args.args:
            se = SecretsEnvironment(environment=e)
            se.environment_create(source=parsed_args.clone_from)
            self.app.LOG.info(
                'environment "{}" '.format(e) +
                '({}) created'.format(se.environment_path())
            )


class EnvironmentsRename(Command):
    """Rename environment"""

    LOG = logging.getLogger(__name__)

    def get_epilog(self):
        return textwrap.dedent("""\
        .. code-block:: console

            $ psec environments list
            +----------------+---------+
            | Environment    | Default |
            +----------------+---------+
            | old            | No      |
            +----------------+---------+
            $ psec environments rename new old
            Source environment "new" does not exist
            $ psec environments rename old new
            environment "old" renamed to "new"
            $ psec environments list
            +----------------+---------+
            | Environment    | Default |
            +----------------+---------+
            | new            | No      |
            +----------------+---------+

        ..""")

    def get_parser(self, prog_name):
        parser = super(EnvironmentsRename, self).get_parser(prog_name)
        parser.add_argument('source',
                            nargs=1,
                            default=None,
                            help='environment to rename')
        parser.add_argument('dest',
                            nargs=1,
                            default=None,
                            help='new environment name')
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('renaming environment')
        basedir = self.app.secrets.secrets_basedir()
        source = parsed_args.source[0]
        dest = parsed_args.dest[0]
        if source is None:
            raise RuntimeError('No source name provided')
        if dest is None:
            raise RuntimeError('No destination name provided')
        if not SecretsEnvironment(environment=source).environment_exists():
            raise RuntimeError(
                'Source environment "{}"'.format(source) +
                ' does not exist')
        if SecretsEnvironment(environment=dest).environment_exists():
            raise RuntimeError(
                'Desitnation environment "{}"'.format(dest) +
                ' already exist')
        os.rename(os.path.join(basedir, source),
                  os.path.join(basedir, dest))
        self.LOG.info(
            'environment "{}" '.format(source) +
            'renamed to "{}"' .format(dest)
        )


class EnvironmentsDefault(Command):
    """Manage default environment via file in cwd"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--unset-default',
            action='store_true',
            dest='unset_default',
            default=False,
            help="Unset localized environment default"
        )
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('managing localized environment default')
        cwd = os.getcwd()
        env_file = os.path.join(cwd, '.python_secrets_environment')
        if parsed_args.unset_default:
            try:
                os.remove(env_file)
            except Exception as e:  # noqa
                self.LOG.info('no default environment was set')
            else:
                self.LOG.info('default environment unset')
        elif parsed_args.environment is None:
            # No environment specified, show current setting
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_string = f.read().replace('\n', '')
                print(env_string)
            else:
                self.LOG.info('default environment is "{}"'.format(
                    SecretsEnvironment().environment()))
        else:
            # Set default to specified environment
            with open(env_file, 'w') as f:
                f.write(parsed_args.environment)
            self.LOG.info('default environment set to "{}"'.format(
                parsed_args.environment))


class EnvironmentsPath(Command):
    """Return path to files and directories for environment"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.add_argument(
            '--json',
            action='store_true',
            dest='json',
            default=False,
            help="Output in JSON (e.g., for Terraform external data source; " +
                 "default: False)"
        )
        parser.add_argument(
            '--tmpdir',
            action='store_true',
            dest='tmpdir',
            default=False,
            help='Create and/or return tmpdir for this environment ' +
                 '(default: False)'
        )
        return parser

    def _print(self, item, use_json=False):
        """Output item, optionally using JSON"""
        if use_json:
            import json
            res = {'path': item}
            print(json.dumps(res))
        else:
            print(item)

    def take_action(self, parsed_args):
        self.LOG.debug('returning environment path')
        e = SecretsEnvironment(environment=self.app.options.environment)
        if parsed_args.tmpdir:
            tmpdir = e.tmpdir_path()
            tmpdir_mode = 0o700
            try:
                os.makedirs(tmpdir, tmpdir_mode)
                self.LOG.info('created tmpdir {}'.format(tmpdir))
            except FileExistsError:
                mode = os.stat(tmpdir).st_mode
                current_mode = S_IMODE(mode)
                if current_mode != tmpdir_mode:
                    os.chmod(tmpdir, tmpdir_mode)
                    self.LOG.info('changed mode on {} from {} to {}'.format(
                        tmpdir, oct(current_mode), oct(tmpdir_mode)))
            finally:
                self._print(tmpdir, parsed_args.json)
        else:
            self._print(e.environment_path(), parsed_args.json)


class EnvironmentsTree(Command):
    """Output tree listing of files/directories in environment"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        default_environment = SecretsEnvironment().environment()
        parser.add_argument(
            '--no-files',
            action='store_true',
            dest='no_files',
            default=False,
            help='Do not include files in listing ' +
                 '(default: False)'
        )
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('outputting environment tree')
        e = SecretsEnvironment(environment=parsed_args.environment)
        e.requires_environment()
        print_files = bool(parsed_args.no_files is False)
        tree(e.environment_path(), print_files=print_files)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
