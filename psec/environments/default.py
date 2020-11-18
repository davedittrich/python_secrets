# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass

from . import default_environment
from . import clear_saved_default_environment
from . import get_saved_default_environment
from . import save_default_environment
from cliff.command import Command
from sys import stdin


class EnvironmentsDefault(Command):
    """Manage default environment via file in cwd."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '--set',
            action='store_true',
            dest='set',
            default=False,
            help="Set localized environment default"
        )
        what.add_argument(
            '--unset',
            action='store_true',
            dest='unset',
            default=False,
            help="Unset localized environment default"
        )
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            If no default is explicitly set, the default that would be
            applied is returned:

            .. code-block:: console

                $ cd ~/git/psec
                $ psec environments default
                [+] default environment is "psec"

            ..

            When listing environments, the default environment that would
            be implicitly used will be identified:

            .. code-block:: console

                $ psec environments list
                +-------------+---------+
                | Environment | Default |
                +-------------+---------+
                | development | No      |
                | testing     | No      |
                | production  | No      |
                +-------------+---------+

            ..

            The following shows setting and unsetting the default:

            .. code-block:: console

                $ psec environments default testing
                [+] default environment set to "testing"
                $ psec environments default
                testing
                $ psec environments list
                +-------------+---------+
                | Environment | Default |
                +-------------+---------+
                | development | No      |
                | testing     | Yes     |
                | production  | No      |
                +-------------+---------+
                $ psec environments default --unset-default
                [+] default environment unset

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] managing localized environment default')
        if parsed_args.unset:
            if parsed_args.environment is not None:
                raise RuntimeError("[-] '--unset' does not take an argument")
            if clear_saved_default_environment():
                self.LOG.info('[+] explicit default environment unset')
            else:
                self.LOG.info('[+] no default environment was set')
        elif parsed_args.set:
            # If it is not possible to interactively ask for environment,
            # just raise an exception.
            if (
                parsed_args.environment is None and not
                    (stdin.isatty() and 'Bullet' in globals())
            ):
                raise RuntimeError('[-] no environment specified')
            # Otherwise, let's prompt for an environment for better UX!
            if parsed_args.environment is not None:
                choice = parsed_args.environment
            else:
                environments = os.listdir(self.app.secrets.secrets_basedir())
                choices = ['<CANCEL>'] + sorted(environments)
                cli = Bullet(prompt="\nChose a new default environment:",
                             choices=choices,
                             indent=0,
                             align=2,
                             margin=1,
                             shift=0,
                             bullet="→",
                             pad_right=5)
                choice = cli.launch()
                # Having second thoughts, eh?
                if choice == "<CANCEL>":
                    self.LOG.info('[-] cancelled setting default')
            if save_default_environment(choice):
                self.LOG.info(
                    f"[+] default environment explicitly set to '{choice}'")
        elif parsed_args.environment is not None:
            print(parsed_args.environment)
        else:
            # No environment specified; show current setting.
            env_string = get_saved_default_environment()
            if env_string is not None:
                if self.app_args.verbose_level > 1:
                    self.LOG.info(
                        "[+] default environment explicitly set "
                        f"to '{env_string}'")
            else:
                # No explicit saved default.
                env_string = default_environment()
                if self.app_args.verbose_level > 1:
                    self.LOG.info(
                        "[+] default environment is implicitly "
                        f"'{env_string}'")
            print(env_string)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
