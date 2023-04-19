# -*- coding: utf-8 -*-

"""
Find defined secrets in environments.
"""

# External imports
import logging
import sys

from pathlib import Path

# External imports
from cliff.lister import Lister

# Local imports
from psec.secrets_environment import SecretsEnvironment
from psec.utils import get_environment_paths


class SecretsFind(Lister):
    """
    Find defined secrets in environments.

    Searches through all environments in the secrets base directory and
    lists those that contain the variable(s) with names matching the
    search terms.  You can search for secrets by value instead using
    the `--value` option flag.  Example::

        $ psec secrets find tanzanite_admin
        [+] searching secrets base directory /Users/dittrich/.secrets
        +-------------+-----------+----------------------------+
        | Environment | Group     | Variable                   |
        +-------------+-----------+----------------------------+
        | tanzanite   | tanzanite | tanzanite_admin_user_email |
        | tanzanite   | tanzanite | tanzanite_admin_password   |
        | tzdocker    | tanzanite | tanzanite_admin_user_email |
        | tzdocker    | tanzanite | tanzanite_admin_password   |
        | tztest      | tanzanite | tanzanite_admin_user_email |
        | tztest      | tanzanite | tanzanite_admin_password   |
        +-------------+-----------+----------------------------+

    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--group',
            action='store',
            dest='group',
            default=None,
            help='Limit searches to this specific group'
        )
        parser.add_argument(
            '--value',
            action='store_true',
            default=False,
            help='The search term is the value to find (not the variable name)'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        data = list()
        columns = ['Environment', 'Group', 'Variable']
        self.logger.info(
            '[+] searching secrets base directory %s',
            self.app.secrets_basedir
        )
        for env_path in get_environment_paths(
            basedir=self.app.secrets_basedir,
        ):
            environment = Path(env_path).name
            se = SecretsEnvironment(
                environment=environment,
                secrets_basedir=self.app.secrets_basedir,
            )
            se.read_secrets_and_descriptions(ignore_errors=True)
            matching = list()
            if parsed_args.value:
                matching = [
                    key for key, value in se.Variable.items()
                    for arg in parsed_args.arg
                    if arg == value
                ]
            else:
                matching = [
                    key for key, value in se.Variable.items()
                    for arg in parsed_args.arg
                    if arg in key
                ]
            for match in matching:
                data.append([environment, se.Group.get(match), match])
        if len(data) < 1:
            args = ','.join([f"'{arg}'" for arg in parsed_args.arg])
            something_something = (
                "with value"
                if parsed_args.value
                else "matching name"
            )
            sys.exit(f"[-] no secrets found {something_something} {args}")
        return columns, data

# vim: set ts=4 sw=4 tw=0 et :
