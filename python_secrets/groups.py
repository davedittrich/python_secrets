# -*- coding: utf-8 -*-

import logging
import os
import shutil

from cliff.lister import Lister
from cliff.command import Command
from python_secrets.secrets import SecretsEnvironment


class GroupsCreate(Command):
    """Create a secrets descriptions group"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsCreate, self).get_parser(prog_name)
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
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating group')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
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
        else:
            with open(new_file, 'w') as f:
                f.writelines(['---\n', '\n', '\n'])
        self.LOG.info('created new group "{}"'.format(
            os.path.splitext(os.path.basename(new_file))[0]))


class GroupsList(Lister):
    """Show a list of secrets groups.

    The names of the groups and number of items are printed by default.
    """

    LOG = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.LOG.debug('listing secret groups')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
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
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('showing secrets in group')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        columns = ('Group', 'Variable')
        data = []
        for group in parsed_args.args:
            for item in self.app.secrets.get_items_from_group(group):
                data.append((group, item))
        return columns, data


class GroupsPath(Command):
    """Return path to secrets descriptions (groups) directory"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsPath, self).get_parser(prog_name)
        default_environment = SecretsEnvironment().environment()
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('returning groups path')
        e = SecretsEnvironment(environment=parsed_args.environment)
        print(e.descriptions_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
