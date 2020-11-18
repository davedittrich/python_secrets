# -*- coding: utf-8 -*-

import argparse
import logging
import psec.secrets
import textwrap

from cliff.command import Command


class GroupsPath(Command):
    """Return path to secrets descriptions (groups) directory."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        default_environment = psec.secrets.SecretsEnvironment().environment()
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
        self.LOG.debug('[*] returning groups path')
        e = psec.secrets.SecretsEnvironment(
                environment=parsed_args.environment)
        print(e.descriptions_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
