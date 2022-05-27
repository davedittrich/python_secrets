# -*- coding: utf-8 -*-

import logging

from cliff.command import Command

from psec.secrets_environment import SecretsEnvironment
from psec.utils import get_default_environment


class GroupsPath(Command):
    """
    Return path to secrets descriptions (groups) directory.

    ::

        $ psec groups path
        /Users/dittrich/.secrets/psec/secrets.d
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        default_environment = get_default_environment()
        parser.add_argument(
            'environment',
            nargs='?',
            default=default_environment
        )
        return parser

    def take_action(self, parsed_args):
        e = SecretsEnvironment(environment=parsed_args.environment)
        print(e.get_descriptions_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
