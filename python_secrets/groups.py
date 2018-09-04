# -*- coding: utf-8 -*-

import logging

from cliff.lister import Lister
from cliff.command import Command
from python_secrets.secrets import SecretsEnvironment


class GroupsList(Lister):
    """Show a list of secrets groups.

    The names of the groups and number of items are printed by default.
    """

    LOG = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.LOG.debug('listing secret groups')
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
        default_environment = self.app.options.environment
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('returning groups path')
        e = SecretsEnvironment(environment=parsed_args.environment)
        print(e.descriptions_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
