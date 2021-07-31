# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment


class GroupsPath(Command):
    """Return path to secrets descriptions (groups) directory."""

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        default_environment = str(SecretsEnvironment())
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        parser.epilog = textwrap.dedent("""
            .. code-block:: console

                $ psec groups path
                /Users/dittrich/.secrets/psec/secrets.d

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.logger.debug('[*] returning groups path')
        e = SecretsEnvironment(environment=parsed_args.environment)
        print(e.descriptions_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
