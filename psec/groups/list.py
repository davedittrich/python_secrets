# -*- coding: utf-8 -*-

import logging
import sys

from cliff.lister import Lister


class GroupsList(Lister):
    """
    Show a list of secrets groups.

    The names of the groups and number of items are printed by default::

        $ psec groups list
        +---------+-------+
        | Group   | Items |
        +---------+-------+
        | jenkins |     1 |
        | myapp   |     4 |
        | trident |     2 |
        +---------+-------+
    """

    logger = logging.getLogger(__name__)

    # def get_parser(self, prog_name):
    #     parser = super().get_parser(prog_name)
    #     return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        se.requires_environment(path_only=True)
        se.read_secrets_descriptions()
        columns = ('Group', 'Items')
        items = {}
        for g in se.get_groups():
            items[g] = se.get_items_from_group(g)
        data = [(k, len(v)) for k, v in items.items()]
        if len(data) == 0:
            sys.exit(1)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
