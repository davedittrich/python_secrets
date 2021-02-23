# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap
from cliff.lister import Lister
import sys


class GroupsList(Lister):
    """Show a list of secrets groups."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            The names of the groups and number of items are printed by default.

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
        self.LOG.debug('[*] listing secret groups')
        self.app.secrets.requires_environment(path_only=True)
        self.app.secrets.read_secrets_descriptions()
        columns = ('Group', 'Items')
        items = {}
        for g in self.app.secrets.get_groups():
            items[g] = self.app.secrets.get_items_from_group(g)
        data = [(k, len(v)) for k, v in items.items()]
        if not len(data):
            sys.exit(1)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
