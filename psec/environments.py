# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import psec.utils
import shutil
import sys
import textwrap

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
    from bullet import Input
    from bullet import colors
except ModuleNotFoundError:
    pass

from cliff.command import Command
from cliff.lister import Lister
from stat import S_IMODE
from sys import stdin


# TODO(dittrich): Improve this?
def _is_default(a, b):
    """
    Return "Yes" or "No" depending on whether e is the default
    environment or not.
    """
    return "Yes" if a == b else "No"


def get_local_default_file():
    """Returns the path to the local identifier file."""
    # TODO(dittrich): May need to do this differently to support
    # Windows file systems.
    return os.path.join(os.getcwd(), '.python_secrets_environment')


def save_default_environment(environment=None):
    """Save environment identifier to local file for defaulting."""
    env_file = get_local_default_file()
    with open(env_file, 'w') as f_out:
        f_out.write('{0}\n'.format(str(environment)))
    return True


def clear_saved_default_environment():
    """Remove saved default environment file."""
    env_file = os.path.join(
        os.getcwd(),
        '.python_secrets_environment')
    if os.path.exists(env_file):
        os.remove(env_file)
        return True
    else:
        return False


def get_saved_default_environment():
    """Return environment ID value saved in local file or None."""
    env_file = get_local_default_file()
    saved_default = None
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            saved_default = f.read().replace('\n', '')
    return saved_default


def default_environment():
    """
    Return the default environment identifier.

    There are multiple ways for a user to specify the environment
    to use for python_secrets commands. Some of these involve
    explicit settings (e.g., via command line option, a
    saved value in the current working directory, or an
    environment variable) or implicitly from the name of the
    current working directory.
    """

    #  NOTE(dittrich): I know this code has multiple return points
    #  but it is simpler and easier to understand this way.
    #
    # Highest priority is inhereted environment variable.
    environment = os.getenv('D2_ENVIRONMENT', None)
    if environment is not None:
        return environment
    #
    # Next is saved file in current working directory.
    local_default = get_saved_default_environment()
    if local_default not in ['', None]:
        return local_default
    #
    # Lowest priority is the directory path basename.
    return os.path.basename(os.getcwd())


class EnvironmentsList(Lister):
    """List the current environments."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsList, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--aliasing',
            action='store_true',
            dest='aliasing',
            default=False,
            help="Include aliasing (default: False)"
        )
        parser.epilog = textwrap.dedent("""
            You can get a list of all available environments at any time,
            including which one would be the default used by sub-commands:

            .. code-block:: console

                $ psec environments list
                +-------------+---------+
                | Environment | Default |
                +-------------+---------+
                | development | No      |
                | testing     | No      |
                | production  | No      |
                +-------------+---------+

            ..

            To see which environments are aliases, use the ``--aliasing``
            option.

            .. code-block:: console

                $ psec -v environments create --alias evaluation testing
                $ psec environments list --aliasing
                +-------------+---------+----------+
                | Environment | Default | AliasFor |
                +-------------+---------+----------+
                | development | No      |          |
                | evaluation  | No      | testing  |
                | testing     | No      |          |
                | production  | No      |          |
                +-------------+---------+----------+

            ..
            """)

        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('listing environment(s)')
        secrets_environment = psec.secrets.SecretsEnvironment()
        default_env = default_environment()
        columns = (['Environment', 'Default'])
        basedir = secrets_environment.secrets_basedir()
        if parsed_args.aliasing:
            columns.append('AliasFor')
        data = list()
        environments = os.listdir(basedir)
        for e in sorted(environments):
            env_path = os.path.join(basedir, e)
            if psec.secrets.is_valid_environment(env_path,
                                                 self.app_args.verbose_level):
                default = _is_default(e, default_env)
                if not parsed_args.aliasing:
                    item = (e, default)
                else:
                    try:
                        alias_for = os.path.basename(os.readlink(env_path))
                    except OSError:
                        alias_for = ''
                    item = (e, default, alias_for)
                data.append(item)
        return columns, data


class EnvironmentsCreate(Command):
    """Create environment(s)."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsCreate, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        how = parser.add_mutually_exclusive_group(required=False)
        how.add_argument(
            '-A', '--alias',
            action='store',
            dest='alias',
            default=None,
            help="Environment to alias (default: None)"
        )
        how.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Environment directory to clone from (default: None)"
        )
        default_environment = psec.secrets.SecretsEnvironment().environment()
        parser.add_argument('env',
                            nargs='*',
                            default=[default_environment])
        parser.epilog = textwrap.dedent("""
            Empty environments can be created as needed, one at a time or
            several at once. Specify the names on the command line as arguments:

            .. code-block:: console

                $ psec environments create development testing production
                environment directory /Users/dittrich/.secrets/development created
                environment directory /Users/dittrich/.secrets/testing created
                environment directory /Users/dittrich/.secrets/production created

            ..

            In some special circumstances, it may be necessary to have one set
            of identical secrets that have different environment names. If
            this happens, you can create an alias (see also the
            ``environments list`` command):

            .. code-block:: console

                $ psec environments create --alias evaluation testing

            ..

            To make it easier to bootstrap an open source project, where the
            use may not be intimately familiar with all necessary secrets
            and settings, you can make their life easier by preparing an
            empty set of secret descriptions that will help prompt the
            user to set them. You can do this following these steps:

            #. Create a template secrets environment directory that contains
               just the secrets definitions. This example uses the template
               found in the `davedittrich/goSecure`_ repository (directory
               https://github.com/davedittrich/goSecure/tree/master/secrets).

            #. Use this template to clone a secrets environment, which will
               initially be empty:

               .. code-block:: console

                   $ psec environments create test --clone-from ~/git/goSecure/secrets
                   new password variable "gosecure_app_password" is not defined
                   new string variable "gosecure_client_ssid" is not defined
                   new string variable "gosecure_client_ssid" is not defined
                   new string variable "gosecure_client_psk" is not defined
                   new password variable "gosecure_pi_password" is not defined
                   new string variable "gosecure_pi_pubkey" is not defined
                   environment directory /Users/dittrich/.secrets/test created

               ..

            .. _davedittrich/goSecure: https://github.com/davedittrich/goSecure

            Note: Directory and file permissions on cloned environments will prevent
            ``other`` from having read/write/execute permissions (i.e., ``o-rwx`` in
            terms of the ``chmod`` command.)
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating environment(s)')
        if parsed_args.alias is not None:
            if len(parsed_args.env) != 1:
                raise RuntimeError('--alias requires one source environment')
            se = psec.secrets.SecretsEnvironment(environment=parsed_args.alias)
            se.environment_create(source=parsed_args.env[0],
                                  alias=True)
            if se.environment_exists():
                self.LOG.info(
                    'environment "{}" '.format(parsed_args.alias) +
                    'aliased to {}'.format(parsed_args.env[0])
                )
            else:
                raise RuntimeError('Failed')
        else:
            # Default to app environment identifier
            if len(parsed_args.env) == 0:
                parsed_args.env = list(self.app.environment)
            for e in parsed_args.env:
                se = psec.secrets.SecretsEnvironment(environment=e)
                se.environment_create(source=parsed_args.clone_from)
                self.LOG.info(
                    'environment "{}" '.format(e) +
                    '({}) created'.format(se.environment_path())
                )


class EnvironmentsDelete(Command):
    """Delete environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsDelete, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Mandatory confirmation (default: False)"
        )
        # default_environment = psec.secrets.SecretsEnvironment().environment()
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Deleting an environment requires use of the ``--force`` flag. If
            not specified, you will be prompted to confirm the environment
            name before it is deleted.

            .. code-block:: console

                $ psec environments delete testenv
                [-] must use "--force" flag to delete an environment.
                [-] the following will be deleted:
                /Users/dittrich/.secrets/testenv
                ├── secrets.d
                │   ├── ansible.yml
                │   ├── ca.yml
                │   ├── consul.yml
                │   ├── do.yml
                │   ├── jenkins.yml
                │   ├── opendkim.yml
                │   ├── rabbitmq.yml
                │   └── trident.yml
                └── token.json

            ..

            .. code-block:: console

                $ psec environments delete --force testenv
                [+] deleted directory path /Users/dittrich/.secrets/testenv

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('deleting environment')
        choice = None
        if parsed_args.environment is not None:
            choice = parsed_args.environment
        elif not (stdin.isatty() and 'Bullet' in globals()):
            # Can't involve user in getting a choice.
            raise RuntimeError('[-] no environment specified to delete')
        else:
            # Give user a chance to choose.
            environments = os.listdir(self.app.secrets.secrets_basedir())
            choices = ['<CANCEL>'] + sorted(environments)
            cli = Bullet(prompt="\nSelect environment to delete:",
                         choices=choices,
                         indent=0,
                         align=2,
                         margin=1,
                         shift=0,
                         bullet="→",
                         pad_right=5)
            choice = cli.launch()
            if choice == "<CANCEL>":
                self.LOG.info('cancelled deleting environment')
                return

        # Environment chosen. Now do we need to confirm?
        e = psec.secrets.SecretsEnvironment(choice)
        env_path = e.environment_path()
        if not parsed_args.force:
            if not stdin.isatty():
                output = psec.utils.tree(env_path,
                                         outfile=None,
                                         print_files=True)
                raise RuntimeError(
                    '[-] must use "--force" flag to delete an environment.\n' +
                    '[-] the following will be deleted: \n' +
                    ''.join([line for line in output]))
            else:
                prompt = 'Type the name "{}" to confirm: '.format(choice)
                cli = Input(prompt,
                            default="",
                            word_color=colors.foreground["yellow"])
                confirm = cli.launch()
                if confirm != choice:
                    self.LOG.info('cancelled deleting environment')
                    return

        # We have confirmation or --force. Now safe to delete.
        shutil.rmtree(env_path)
        self.LOG.info('[+] deleted directory path ' +
                      '{}'.format(env_path))


class EnvironmentsRename(Command):
    """Rename environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsRename, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('source',
                            nargs=1,
                            default=None,
                            help='environment to rename')
        parser.add_argument('dest',
                            nargs=1,
                            default=None,
                            help='new environment name')
        parser.epilog = textwrap.dedent("""
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

            ..
            """)

        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('renaming environment')
        basedir = self.app.secrets.secrets_basedir()
        source = parsed_args.source[0]
        source_path = os.path.join(basedir, source)
        dest = parsed_args.dest[0]
        dest_path = os.path.join(basedir, dest)
        if source is None:
            raise RuntimeError('No source name provided')
        if dest is None:
            raise RuntimeError('No destination name provided')
        if not psec.secrets.SecretsEnvironment(
                environment=source).environment_exists():
            raise RuntimeError(
                'Source environment "{}"'.format(source) +
                ' does not exist')
        if psec.secrets.SecretsEnvironment(
                environment=dest).environment_exists():
            raise RuntimeError(
                'Desitnation environment "{}"'.format(dest) +
                ' already exist')
        os.rename(source_path, dest_path)
        self.LOG.info(
            'environment "{}" '.format(source) +
            'renamed to "{}"' .format(dest)
        )


class EnvironmentsDefault(Command):
    """Manage default environment via file in cwd."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '--set',
            action='store_true',
            dest='set',
            default=False,
            help="Set localized environment default"
        )
        what.add_argument(
            '--unset',
            action='store_true',
            dest='unset',
            default=False,
            help="Unset localized environment default"
        )
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            If no default is explicitly set, the default that would be
            applied is returned:

            .. code-block:: console

                $ cd ~/git/psec
                $ psec environments default
                default environment is "psec"

            ..

            When listing environments, the default environment that would
            be implicitly used will be identified:

            .. code-block:: console

                $ psec environments list
                +-------------+---------+
                | Environment | Default |
                +-------------+---------+
                | development | No      |
                | testing     | No      |
                | production  | No      |
                +-------------+---------+

            ..

            The following shows setting and unsetting the default:

            .. code-block:: console

                $ psec environments default testing
                default environment set to "testing"
                $ psec environments default
                testing
                $ psec environments list
                +-------------+---------+
                | Environment | Default |
                +-------------+---------+
                | development | No      |
                | testing     | Yes     |
                | production  | No      |
                +-------------+---------+
                $ psec environments default --unset-default
                default environment unset

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('managing localized environment default')
        if parsed_args.unset:
            if parsed_args.environment is not None:
                raise RuntimeError('--unset does not take an argument')
            if clear_saved_default_environment():
                self.LOG.info('explicit default environment unset')
            else:
                self.LOG.info('no default environment was set')
        elif parsed_args.set:
            # If it is not possible to interactively ask for environment,
            # just raise an exception.
            if (
                parsed_args.environment is None and not
                    (stdin.isatty() and 'Bullet' in globals())
            ):
                raise RuntimeError('[-] no environment specified')
            # Otherwise, let's prompt for an environment for better UX!
            if parsed_args.environment is not None:
                choice = parsed_args.environment
            else:
                environments = os.listdir(self.app.secrets.secrets_basedir())
                choices = ['<CANCEL>'] + sorted(environments)
                cli = Bullet(prompt="\nChose a new default environment:",
                             choices=choices,
                             indent=0,
                             align=2,
                             margin=1,
                             shift=0,
                             bullet="→",
                             pad_right=5)
                choice = cli.launch()
                # Having second thoughts, eh?
                if choice == "<CANCEL>":
                    self.LOG.info('cancelled setting default')
            if save_default_environment(choice):
                self.LOG.info(('default environment set explicitly to '
                               f'"{choice}"'))
        elif parsed_args.environment is not None:
            print(parsed_args.environment)
        else:
            # No environment specified; show current setting.
            env_string = get_saved_default_environment()
            if env_string is not None:
                if self.app_args.verbose_level > 1:
                    self.LOG.info(('default environment set explicitly to '
                                   f'"{env_string}"'))
            else:
                # No explicit saved default.
                env_string = default_environment()
                if self.app_args.verbose_level > 1:
                    self.LOG.info(('default environment is implicitly '
                                   f'"{env_string}"'))
            print(env_string)


class EnvironmentsPath(Command):
    """Return path to files and directories for environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--create',
            action='store_true',
            dest='create',
            default=False,
            help=("Create the directory path if it does not yet exist "
                  "(default: False)")
        )
        parser.add_argument(
            '--exists',
            action='store_true',
            dest='exists',
            default=False,
            help="Check to see if environment exists and" +
                 "return exit code (0==exists, 1==not)"
        )
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
        parser.add_argument('subdir',
                            nargs='*',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Provides the full absolute path to the environment directory
            for the environment and any specified subdirectories.

            .. code-block:: console

                $ psec environments path
                /Users/dittrich/.secrets/psec
                $ psec environments path -e goSecure
                /Users/dittrich/.secrets/goSecure

            ..

            Using the ``--exists`` option will just return ``0`` if the path
            exists, or ``1`` if it does not. No path is printed on stdout.

            Using the ``--tmpdir`` option will return the path to the
            temporary directory for the environment. If it does not already
            exist, it will be created so it is ready for use.

            To append subdirectory components, provide them as arguments and
            they will be concatenated with the appropriate OS path separator.

            .. code-block:: console

                $ psec environments path -e goSecure configs
                /Users/dittrich/.secrets/goSecure/configs

            ..

            To ensure the directory path specified by command line arguments
            is present, use the ``--create`` option.

            """)
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
        environment = self.app.options.environment
        e = psec.secrets.SecretsEnvironment(environment)
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
            base_path = e.environment_path()
            subdir = parsed_args.subdir
            full_path = base_path if subdir is None \
                else os.path.join(base_path, *subdir)
            if not os.path.exists(full_path) and parsed_args.create:
                mode = 0o700
                os.makedirs(full_path, mode)
                if self.app_args.verbose_level > 1:
                    self.LOG.info(f"created {full_path}")
            if parsed_args.exists:
                # Just check existance and return result
                exists = os.path.exists(full_path)
                if self.app_args.verbose_level > 1:
                    status = "exists" if exists else "does not exist"
                    self.LOG.info('environment path' +
                                  '"{}" '.format(full_path) +
                                  '{}'.format(status)
                                  )
                return 0 if exists else 1
            else:
                self._print(full_path, parsed_args.json)


class EnvironmentsTree(Command):
    """Output tree listing of files/directories in environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
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
                            default=None)
        parser.epilog = textwrap.dedent("""
            The ``environments tree`` command produces output similar
            to the Unix ``tree`` command:

            .. code-block:: console

                $ psec -e d2 environments tree
                /Users/dittrich/.secrets/d2
                ├── backups
                │   ├── black.secretsmgmt.tk
                │   │   ├── letsencrypt_2018-04-06T23:36:58PDT.tgz
                │   │   └── letsencrypt_2018-04-25T16:32:20PDT.tgz
                │   ├── green.secretsmgmt.tk
                │   │   ├── letsencrypt_2018-04-06T23:45:49PDT.tgz
                │   │   └── letsencrypt_2018-04-25T16:32:20PDT.tgz
                │   ├── purple.secretsmgmt.tk
                │   │   ├── letsencrypt_2018-04-25T16:32:20PDT.tgz
                │   │   ├── trident_2018-01-31T23:38:48PST.tar.bz2
                │   │   └── trident_2018-02-04T20:05:33PST.tar.bz2
                │   └── red.secretsmgmt.tk
                │       ├── letsencrypt_2018-04-06T23:45:49PDT.tgz
                │       └── letsencrypt_2018-04-25T16:32:20PDT.tgz
                ├── dittrich.asc
                ├── keys
                │   └── opendkim
                │       └── secretsmgmt.tk
                │           ├── 201801.private
                │           ├── 201801.txt
                │           ├── 201802.private
                │           └── 201802.txt
                ├── secrets.d
                │   ├── ca.yml
                │   ├── consul.yml
                │   ├── jenkins.yml
                │   ├── rabbitmq.yml
                │   ├── trident.yml
                │   ├── vncserver.yml
                │   └── zookeper.yml
                ├── secrets.yml
                └── vault_password.txt

            ..

            To just see the directory structure and not files, add
            the ``--no-files`` option:

            .. code-block:: console

                $ psec -e d2 environments tree --no-files
                /Users/dittrich/.secrets/d2
                ├── backups
                │   ├── black.secretsmgmt.tk
                │   ├── green.secretsmgmt.tk
                │   ├── purple.secretsmgmt.tk
                │   └── red.secretsmgmt.tk
                ├── keys
                │   └── opendkim
                │       └── secretsmgmt.tk
                └── secrets.d

            ..

            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('outputting environment tree')
        environment = parsed_args.environment
        if environment is None:
            environment = self.app.options.environment
        e = psec.secrets.SecretsEnvironment(
            environment=environment)
        e.requires_environment()
        print_files = bool(parsed_args.no_files is False)
        psec.utils.atree(e.environment_path(),
                         print_files=print_files,
                         outfile=sys.stdout)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
