# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.utils
import psec.secrets
import shutil
import textwrap

from cliff.lister import Lister
from cliff.command import Command


class GroupsCreate(Command):
    """Create a secrets descriptions group"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsCreate, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Group descriptions file to clone from (default: None)"
        )
        parser.add_argument('group',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            When integrating a new open source tool or project, you can
            create a new group and clone its secrets descriptions. This
            does not copy any values, just the descriptions, allowing
            the current environment to manage its own values.

            .. code-block:: console

                $ psec groups create newgroup --clone-from ~/git/goSecure/secrets/secrets.d/gosecure.yml
                created new group "newgroup"
                $ psec groups list
                +----------+-------+
                | Group    | Items |
                +----------+-------+
                | jenkins  |     1 |
                | myapp    |     4 |
                | newgroup |    12 |
                | trident  |     2 |
                +----------+-------+

            ..

            Note: Directory and file permissions on cloned groups will prevent
            ``other`` from having read/write/execute permissions (i.e., ``o-rwx``
            in terms of the ``chmod`` command.)
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating group')
        # An empty environment that exists is OK for this.
        self.app.secrets.requires_environment(path_only=True)
        self.app.secrets.read_secrets_descriptions()
        if parsed_args.clone_from is None and parsed_args.group is None:
            raise RuntimeError('No group name specified')
        dest_dir = self.app.secrets.descriptions_path()
        if parsed_args.clone_from is not None:
            data = self.app.secrets.get_descriptions(parsed_args.clone_from)
            self.app.secrets.check_duplicates(data)
            dest_file = os.path.basename(parsed_args.clone_from)
            if not os.path.exists(parsed_args.clone_from):
                raise RuntimeError('Group description file ' +
                                   '"{}" '.format(parsed_args.clone_from) +
                                   'does not exist')
        if parsed_args.group is not None:
            dest_file = parsed_args.group + '.yml'
        new_file = os.path.join(dest_dir, dest_file)
        if os.path.exists(new_file):
            raise RuntimeError('Group file "{}" '.format(new_file) +
                               'already exists')
        if parsed_args.clone_from is not None:
            shutil.copy2(parsed_args.clone_from, new_file)
            psec.utils.remove_other_perms(new_file)
        else:
            with open(new_file, 'w') as f:
                f.writelines(['---\n', '\n', '\n'])
            psec.utils.remove_other_perms(new_file)
        self.LOG.info('created new group "{}"'.format(
            os.path.splitext(os.path.basename(new_file))[0]))


class GroupsList(Lister):
    """Show a list of secrets groups.

    The names of the groups and number of items are printed by default.
    """

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsList, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            .. code-block:: console

                $ psec groups list
                +---------+-------+
                | Group   | Items |
                +---------+-------+
                | jenkins |     1 |
                | myapp   |     4 |
                | trident |     2 |
                +---------+-------+

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('listing secret groups')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_descriptions()
        items = {}
        for g in self.app.secrets.get_groups():
            items[g] = self.app.secrets.get_items_from_group(g)
        return (('Group', 'Items'),
                ((k, len(v)) for k, v in items.items())
                )


class GroupsShow(Lister):
    """Show a list of secrets in a group.

    The names of the groups and number of items are printed by default.
    """

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsShow, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('group', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            The variables in one or more groups can be shown with
            the ``groups show`` command:

            .. code-block:: console

                $ psec groups show trident myapp
                +---------+-----------------------+
                | Group   | Variable              |
                +---------+-----------------------+
                | trident | trident_sysadmin_pass |
                | trident | trident_db_pass       |
                | myapp   | myapp_pi_password     |
                | myapp   | myapp_app_password    |
                | myapp   | myapp_client_psk      |
                | myapp   | myapp_client_ssid     |
                +---------+-----------------------+

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('showing secrets in group')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_descriptions()
        columns = ('Group', 'Variable')
        data = []
        for group in parsed_args.group:
            for item in self.app.secrets.get_items_from_group(group):
                data.append((group, item))
        return columns, data


class GroupsPath(Command):
    """Return path to secrets descriptions (groups) directory"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsPath, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        default_environment = psec.secrets.SecretsEnvironment().environment()
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        parser.epilog = textwrap.dedent("""
            .. code-block:: console

                $ psec groups path
                /Users/dittrich/.secrets/psec/secrets.d

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('returning groups path')
        e = psec.secrets.SecretsEnvironment(
                environment=parsed_args.environment)
        print(e.descriptions_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
