# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import shutil
import textwrap

from cliff.command import Command
from psec.utils import remove_other_perms


class GroupsCreate(Command):
    """Create a secrets descriptions group."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
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

                $ psec groups create newgroup --clone-from ~/git/goSecure/secrets/secrets.d/gosecure.json
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
                    '{0}.json'.format(parsed_args.group)
                )
                descriptions = clonefrom_environment.read_descriptions(
                    group_source)
            else:
                group_source = parsed_args.clone_from
                descriptions = self.app.secrets.read_descriptions(group_source)
            self.app.secrets.check_duplicates(descriptions)
            dest_file = os.path.basename(group_source)
            if not os.path.exists(group_source):
                raise RuntimeError('Group description file ' +
                                   '"{}" '.format(group_source) +
                                   'does not exist')
        elif parsed_args.group is not None:
            if not parsed_args.group.endswith('.json'):
                dest_file = parsed_args.group + '.json'
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


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
