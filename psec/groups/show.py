# -*- coding: utf-8 -*-

import logging
import sys

from cliff.lister import Lister


class GroupsShow(Lister):
    """
    Show a list of secrets in a group.

    Show the group name and number of items in the group for one or more
    groups::

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
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'group',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_descriptions()
        columns = ('Group', 'Variable')
        data = []
        for group in parsed_args.group:
            for item in se.get_items_from_group(group):
                data.append((group, item))
        if len(data) == 0:
            sys.exit(1)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
