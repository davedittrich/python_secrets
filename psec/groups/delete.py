# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
    from bullet import Input
    from bullet import colors
except ModuleNotFoundError:
    pass
from cliff.command import Command
from psec.utils import safe_delete_file
from sys import stdin


class GroupsDelete(Command):
    """Delete a secrets descriptions group."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Mandatory confirmation (default: False)"
        )
        parser.add_argument('group',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Deletes a group of secrets and variables by removing them from
            the secrets environment and deleting their descriptions file.

            If the ``--force`` ption is not specified, you will be prompted
            to confirm the group name before it is deleted.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] deleting group')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_descriptions()
        group = parsed_args.group
        groups = self.app.secrets.get_groups()
        choice = None

        if parsed_args.group is not None:
            choice = parsed_args.group
        elif not (stdin.isatty() and 'Bullet' in globals()):
            # Can't involve user in getting a choice.
            raise RuntimeError('[-] no group specified to delete')
        else:
            # Give user a chance to choose.
            choices = ['<CANCEL>'] + sorted(groups)
            cli = Bullet(prompt="\nSelect group to delete:",
                         choices=choices,
                         indent=0,
                         align=2,
                         margin=1,
                         shift=0,
                         bullet="→",
                         pad_right=5)
            choice = cli.launch()
            if choice == "<CANCEL>":
                self.LOG.info('[-] cancelled deleting group')
                return

        # Group chosen. Now do we need to confirm?
        if not parsed_args.force:
            if not stdin.isatty():
                raise RuntimeError(
                    '[-] must use "--force" flag to delete a group.')
            else:
                prompt = f"Type the name '{choice}' to confirm: "
                cli = Input(prompt,
                            default="",
                            word_color=colors.foreground["yellow"])
                confirm = cli.launch()
                if confirm != choice:
                    self.LOG.info('[-] cancelled deleting group')
                    return

        group_file = self.app.secrets.descriptions_path(group=group)
        if not os.path.exists(group_file):
            raise RuntimeError(
                f"[-] group file '{group_file}' does not exist")
        # Delete secrets from group.
        secrets = self.app.secrets.get_items_from_group(choice)
        for secret in secrets:
            self.app.secrets.delete_secret(secret)
        # Delete group descriptions.
        safe_delete_file(group_file)
        self.LOG.info(
            f"[+] deleted secrets group '{choice}' ({group_file})")


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
