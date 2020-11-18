# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import psec.utils
import shutil
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
from sys import stdin


class EnvironmentsDelete(Command):
    """Delete environment."""

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
        # default_environment = psec.secrets.SecretsEnvironment().environment()
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Deleting an environment requires use of the ``--force`` flag. If
            not specified, you will be prompted to confirm the environment
            name before it is deleted.

            .. code-block:: console

                $ psec environments delete testenv
                [-] must use '--force' flag to delete an environment.
                [-] the following will be deleted:
                /Users/dittrich/.secrets/testenv
                ├── secrets.d
                │   ├── ansible.json
                │   ├── ca.json
                │   ├── consul.json
                │   ├── do.json
                │   ├── jenkins.json
                │   ├── opendkim.json
                │   ├── rabbitmq.json
                │   └── trident.json
                └── token.json

            ..

            .. code-block:: console

                $ psec environments delete --force testenv
                [+] deleted directory path /Users/dittrich/.secrets/testenv

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] deleting environment')
        choice = None
        if parsed_args.environment is not None:
            choice = parsed_args.environment
        elif not (stdin.isatty() and 'Bullet' in globals()):
            # Can't involve user in getting a choice.
            raise RuntimeError('[-] no environment specified to delete')
        else:
            # Give user a chance to choose.
            environments = os.listdir(self.app.secrets.secrets_basedir())
            choices = ['<CANCEL>'] + sorted(environments)
            cli = Bullet(prompt="\nSelect environment to delete:",
                         choices=choices,
                         indent=0,
                         align=2,
                         margin=1,
                         shift=0,
                         bullet="→",
                         pad_right=5)
            choice = cli.launch()
            if choice == "<CANCEL>":
                self.LOG.info('[-] cancelled deleting environment')
                return

        # Environment chosen. Now do we need to confirm?
        e = psec.secrets.SecretsEnvironment(choice)
        env_path = e.environment_path()
        if not parsed_args.force:
            if not stdin.isatty():
                output = psec.utils.atree(env_path,
                                          outfile=None,
                                          print_files=True)
                raise RuntimeError(
                    "[-] must use '--force' flag to delete an environment.\n"
                    "[-] the following will be deleted: \n"
                    f"{''.join([line for line in output])}"
                )
            else:
                prompt = f"Type the name '{choice}' to confirm: "
                cli = Input(prompt,
                            default="",
                            word_color=colors.foreground["yellow"])
                confirm = cli.launch()
                if confirm != choice:
                    self.LOG.info('[-] cancelled deleting environment')
                    return

        # We have confirmation or --force. Now safe to delete.
        # TODO(dittrich): Use safe_delete_file over file list
        shutil.rmtree(env_path)
        self.LOG.info(f"[+] deleted directory path '{env_path}")


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
