# -*- coding: utf-8 -*-

import logging

from cliff.lister import Lister


class GroupsList(Lister):
    """Show a list of secrets groups.

    The names of the groups and number of items are printed by default.
    """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('listing secret groups')
        items = {}
        for g in self.app.get_groups():
            items[g] = self.app.get_items_from_group(g)
        return (('Group', 'Items'),
                ((k, len(v)) for k, v in items.items())
                )


class GroupsShow(Lister):
    """Show a list of secrets in a group.

    The names of the groups and number of items are printed by default.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GroupsShow, self).get_parser(prog_name)
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('showing secrets in group')
        columns = ('Group', 'Variable')
        data = []
        for group in parsed_args.args:
            for item in self.app.get_items_from_group(group):
                data.append((group, item))
        return columns, data

# EOF
