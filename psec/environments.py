# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.command import Command
from cliff.lister import Lister
from psec.secrets import is_valid_environment
from psec.secrets import SecretsEnvironment
from psec.utils import tree
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
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
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
            """)

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
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Environment directory to clone from (default: None)"
        )
        parser.add_argument('env',
                            nargs='*',
                            default=[SecretsEnvironment().environment()])
        parser.epilog = textwrap.dedent("""

            A set of secrets for an open source project can be bootstrapped
            using the following steps:

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

            If you want to create more than one environment at once, you will
            have to specify all of the names on the command line as arguments:

            .. code-block:: console

                $ psec environments create development testing production
                environment directory /Users/dittrich/.secrets/development created
                environment directory /Users/dittrich/.secrets/testing created
                environment directory /Users/dittrich/.secrets/production created

            ..

            .. _davedittrich/goSecure: https://github.com/davedittrich/goSecure
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating environment(s)')
        # basedir = self.app.get_secrets_basedir()
        if len(parsed_args.env) == 0:
            parsed_args.env = list(self.app.environment)
        for e in parsed_args.env:
            se = SecretsEnvironment(environment=e)
            se.environment_create(source=parsed_args.clone_from)
            self.app.LOG.info(
                'environment "{}" '.format(e) +
                '({}) created'.format(se.environment_path())
            )


class EnvironmentsRename(Command):
    """Rename environment"""

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
        cwd = os.getcwd()
        env_file = os.path.join(cwd, '.python_secrets_environment')
        if parsed_args.unset:
            try:
                os.remove(env_file)
            except Exception as e:  # noqa
                self.LOG.info('no default environment was set')
            else:
                self.LOG.info('default environment unset')
        elif parsed_args.set:
            # Set default to specified environment
            default_env = parsed_args.environment
            if default_env is None:
                default_env = SecretsEnvironment().environment()
            with open(env_file, 'w') as f:
                f.write(default_env)
            self.LOG.info('default environment set to "{}"'.format(
                default_env))
        elif parsed_args.environment is None:
            # No environment specified, show current setting
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_string = f.read().replace('\n', '')
                print(env_string)
            else:
                self.LOG.info('default environment is "{}"'.format(
                    SecretsEnvironment().environment()))


class EnvironmentsPath(Command):
    """Return path to files and directories for environment"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
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
        parser.epilog = textwrap.dedent("""
            Provides the full absolute path to the environment directory
            for the environment.

            .. code-block:: console

                $ psec environments path
                /Users/dittrich/.secrets/psec
                $ psec environments path -e goSecure
                /Users/dittrich/.secrets/goSecure

            ..

            Using the ``--tmpdir`` option will return the path to the
            temporary directory for the environment. If it does not already
            exist, it will be created so it is ready for use.
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
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
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
        e = SecretsEnvironment(environment=parsed_args.environment)
        e.requires_environment()
        print_files = bool(parsed_args.no_files is False)
        tree(e.environment_path(), print_files=print_files)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
