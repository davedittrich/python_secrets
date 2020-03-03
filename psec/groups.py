# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import shutil
import textwrap

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
    from bullet import Input
    from bullet import colors
except ModuleNotFoundError:
    pass
from cliff.lister import Lister
from cliff.command import Command
from psec.utils import remove_other_perms
from sys import stdin


class GroupsCreate(Command):
    """Create a secrets descriptions group."""

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
        # Cloning inherits name from file, otherwise name required.
        # Source group file may be determined from environment.
        group_source = None
        if parsed_args.clone_from is not None:
            # Cloning a group from an existing environment?
            clonefrom_environment = psec.secrets.SecretsEnvironment(
                environment=parsed_args.clone_from
            )
            clonefrom_environment.read_secrets_descriptions()
            if parsed_args.group in clonefrom_environment.get_groups():
                group_source = os.path.join(
                    clonefrom_environment.descriptions_path(),
                    '{0}.yml'.format(parsed_args.group)
                )
                descriptions = clonefrom_environment.get_descriptions(
                    group_source)
            else:
                group_source = parsed_args.clone_from
                descriptions = self.app.secrets.get_descriptions(group_source)
            self.app.secrets.check_duplicates(descriptions)
            dest_file = os.path.basename(group_source)
            if not os.path.exists(group_source):
                raise RuntimeError('Group description file ' +
                                   '"{}" '.format(group_source) +
                                   'does not exist')
        elif parsed_args.group is not None:
            if not parsed_args.group.endswith('.yml'):
                dest_file = parsed_args.group + '.yml'
            else:
                dest_file = parsed_args.group
        else:
            raise RuntimeError('No group name or file specified')

        dest_dir = self.app.secrets.descriptions_path()
        new_file = os.path.join(dest_dir, dest_file)
        if os.path.exists(new_file):
            raise RuntimeError('Group file "{}" '.format(new_file) +
                               'already exists')
        if parsed_args.clone_from is not None:
            shutil.copy2(group_source, new_file)
            remove_other_perms(new_file)
        else:
            with open(new_file, 'w') as f:
                f.writelines(['---\n', '\n', '\n'])
            remove_other_perms(new_file)
        self.LOG.info('created new group "{}"'.format(
            os.path.splitext(os.path.basename(new_file))[0]))


class GroupsDelete(Command):
    """Delete a secrets descriptions group."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Mandatory confirmation (default: False)"
        )
        parser.add_argument('group',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Deletes a group of variables by removing them from the secrets
            environment and deleting their descriptions.  If the ``--force``
            option is not specified, you will be prompted to confirm the
            group name before it is deleted.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('deleting group')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_descriptions()
        groups = self.app.secrets.get_groups()
        choice = None

        if parsed_args.group is not None:
            choice = parsed_args.group
        elif not (stdin.isatty() and 'Bullet' in globals()):
            # Can't involve user in getting a choice.
            raise RuntimeError('[-] no group specified to delete')
        else:
            # Give user a chance to choose.
            choices = ['<CANCEL>'] + sorted(groups)
            cli = Bullet(prompt="\nSelect group to delete:",
                         choices=choices,
                         indent=0,
                         align=2,
                         margin=1,
                         shift=0,
                         bullet="→",
                         pad_right=5)
            choice = cli.launch()
            if choice == "<CANCEL>":
                self.LOG.info('cancelled deleting group')
                return

        # Group chosen. Now do we need to confirm?
        if not parsed_args.force:
            if not stdin.isatty():
                raise RuntimeError(
                    '[-] must use "--force" flag to delete a group.')
            else:
                prompt = 'Type the name "{}" to confirm: '.format(choice)
                cli = Input(prompt,
                            default="",
                            word_color=colors.foreground["yellow"])
                confirm = cli.launch()
                if confirm != choice:
                    self.LOG.info('cancelled deleting group')
                    return

        descriptions_path = self.app.secrets.descriptions_path()
        group_file = os.path.join(descriptions_path, '{0}.yml'.format(choice))
        if not os.path.exists(group_file):
            raise RuntimeError(('Group file "{}" does not '
                                'exist').format(group_file))
        # Delete secrets from group.
        secrets = self.app.secrets.get_items_from_group(choice)
        for secret in secrets:
            self.app.secrets.delete_secret(secret)
        # Delete group descriptions.
        os.unlink(group_file)
        self.LOG.info('[+] deleted secrets group "{0}"'.format(choice))


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
    """Return path to secrets descriptions (groups) directory."""

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
