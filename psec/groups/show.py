# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister


class GroupsShow(Lister):
    """Show a list of secrets in a group."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('group', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            Show the group name and number of items in the
            group for one or more groups:

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
        self.LOG.debug('[*] showing secrets in group')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_descriptions()
        columns = ('Group', 'Variable')
        data = []
        for group in parsed_args.group:
            for item in self.app.secrets.get_items_from_group(group):
                data.append((group, item))
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
