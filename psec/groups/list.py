# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap
from cliff.lister import Lister


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
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_descriptions()
        items = {}
        for g in self.app.secrets.get_groups():
            items[g] = self.app.secrets.get_items_from_group(g)
        return (('Group', 'Items'),
                ((k, len(v)) for k, v in items.items())
                )


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
