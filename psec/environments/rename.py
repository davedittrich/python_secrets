# -*- coding: utf-8 -*-

import logging
import os

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment


class EnvironmentsRename(Command):
    """
    Rename environment.

    Just like `mv`, renames an environment from the name specified by the
    first argument to that of the second argument::

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
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'source',
            nargs=1,
            default=None,
            help='environment to rename'
        )
        parser.add_argument(
            'dest',
            nargs=1,
            default=None,
            help='new environment name'
        )
        return parser

    def take_action(self, parsed_args):
        basedir = self.app.secrets.get_secrets_basedir()
        source = parsed_args.source[0]
        source_path = os.path.join(basedir, source)
        dest = parsed_args.dest[0]
        dest_path = os.path.join(basedir, dest)
        if source is None:
            raise RuntimeError('[-] no source name provided')
        if dest is None:
            raise RuntimeError('[-] no destination name provided')
        if not SecretsEnvironment(
                environment=source).environment_exists():
            raise RuntimeError(
                f"[-] source environment '{source}' does not exist")
        if SecretsEnvironment(
                environment=dest).environment_exists():
            raise RuntimeError(
                f"[-] destination environment '{dest}' already exist")
        os.rename(source_path, dest_path)
        self.logger.info(
            "[+] environment '%s' renamed to '%s'",
            source,
            dest
        )


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
