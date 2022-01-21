# -*- coding: utf-8 -*-

import logging
import os

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
    """
    Delete a secrets descriptions group.

    Deletes a group of secrets and variables by removing them from
    the secrets environment and deleting their descriptions file.

    If the ``--force`` option is not specified, you will be prompted
    to confirm the group name before it is deleted.
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Mandatory confirmation'
        )
        parser.add_argument(
            'group',
            nargs='?',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_descriptions()
        group = parsed_args.group
        groups = se.get_groups()
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
                self.logger.info('[-] cancelled deleting group')
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
                    self.logger.info('[-] cancelled deleting group')
                    return

        group_file = se.get_descriptions_path(group=group)
        if not os.path.exists(group_file):
            raise RuntimeError(
                f"[-] group file '{group_file}' does not exist")
        # Delete secrets from group.
        secrets = se.get_items_from_group(choice)
        for secret in secrets:
            se.delete_secret(secret)
        # Delete group descriptions.
        safe_delete_file(group_file)
        self.logger.info(
            "[+] deleted secrets group '%s' (%s)",
            choice,
            group_file
        )


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
