# -*- coding: utf-8 -*-

import logging
import shutil
import sys
from sys import stdin

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
    from bullet import Input
    from bullet import colors
except ModuleNotFoundError:
    pass

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment
from psec.utils import (
    get_environment_paths,
    atree,
)


class EnvironmentsDelete(Command):
    """
    Delete environment.

    Deleting an environment requires explicitly naming the environment
    to delete and confirmation from the user. This is done in one of
    two ways: by prompting the user to confirm the environment to delete,
    or by requiring the ``--force`` option flag be set along with the name.

    When this command is run in a terminal shell (i.e., with a TTY),
    the user will be asked to type the name again to confirm the operation::

        $ psec environments delete testenv
        Type the name 'testenv' to confirm: testenv
        [+] deleted directory path '/Users/dittrich/.secrets/testenv'


    If no TTY is present (i.e., a shell script running in the background),
    an exception is raised that includes the files that will be deleted
    and explaining how to force the deletion::

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


    The ``--force`` flag will allow deletion of the environment::

        $ psec environments delete --force testenv
        [+] deleted directory path /Users/dittrich/.secrets/testenv
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
            'environment',
            nargs='?',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        choice = None
        if parsed_args.environment is not None:
            choice = parsed_args.environment
        elif stdin.isatty() and 'Bullet' in globals():
            # Give user a chance to choose.
            environments = [
                fpath.name for fpath in get_environment_paths(
                    basedir=self.app.secrets_basedir
                )
            ]
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
                self.logger.info('[-] cancelled deleting environment')
                return
        else:
            # Can't involve user in getting a choice.
            sys.exit('[-] no environment specified to delete')
        # Environment chosen. Now do we need to confirm?
        e = SecretsEnvironment(choice)
        env_path = e.get_environment_path()
        if not parsed_args.force:
            if not stdin.isatty():
                output = atree(
                    env_path,
                    outfile=None,
                    print_files=True
                )
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
                    self.logger.info('[-] cancelled deleting environment')
                    return
        # We have confirmation or --force. Now safe to delete.
        # TODO(dittrich): Use safe_delete_file over file list
        if env_path.is_symlink():
            env_path.unlink()
            self.logger.info("[+] deleted alias '%s'", env_path)
        else:
            shutil.rmtree(env_path)
            self.logger.info("[+] deleted directory path '%s'", env_path)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
