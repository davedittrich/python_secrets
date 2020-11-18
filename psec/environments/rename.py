# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import psec.utils
import textwrap

from cliff.command import Command


class EnvironmentsRename(Command):
    """Rename environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('source',
                            nargs=1,
                            default=None,
                            help='environment to rename')
        parser.add_argument('dest',
                            nargs=1,
                            default=None,
                            help='new environment name')
        parser.epilog = textwrap.dedent("""
            .. code-block:: console

                $ psec environments list
                +----------------+---------+
                | Environment    | Default |
                +----------------+---------+
                | old            | No      |
                +----------------+---------+
                $ psec environments rename new old
                [-] source environment "new" does not exist
                $ psec environments rename old new
                [+] environment "old" renamed to "new"
                $ psec environments list
                +----------------+---------+
                | Environment    | Default |
                +----------------+---------+
                | new            | No      |
                +----------------+---------+

            ..
            """)

        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] renaming environment')
        basedir = self.app.secrets.secrets_basedir()
        source = parsed_args.source[0]
        source_path = os.path.join(basedir, source)
        dest = parsed_args.dest[0]
        dest_path = os.path.join(basedir, dest)
        if source is None:
            raise RuntimeError('[-] no source name provided')
        if dest is None:
            raise RuntimeError('[-] no destination name provided')
        if not psec.secrets.SecretsEnvironment(
                environment=source).environment_exists():
            raise RuntimeError(
                f"[-] source environment '{source}' does not exist")
        if psec.secrets.SecretsEnvironment(
                environment=dest).environment_exists():
            raise RuntimeError(
                f"[-] destination environment '{dest}' already exist")
        os.rename(source_path, dest_path)
        self.LOG.info(
            f"[+] environment '{source}' renamed to '{dest}'")


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
