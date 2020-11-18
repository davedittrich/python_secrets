# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap
import shlex

from cliff.command import Command
from subprocess import call  # nosec

# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.


class Run(Command):
    """Run a command using exported secrets."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('arg',
                            nargs='*',
                            help='command arguments ' +
                                 '(default: "psec run --help")',
                            default=['psec', 'run', '--help'])
        parser.epilog = textwrap.dedent("""
            This option is used to run a command, just like a normal Bash
            command line. While this may not seem important, when combined
            with the ``-e`` option to export an environment's variables into
            the shells environment, it becomes very powerful. If you use this
            option to run a program like ``byobu``, every shell that is
            subsequently spawned will inherit these environment variables
            (which in turn are inherited by programs like Ansible, Terraform,
            etc.)

            If no arguments are specified, the ``--help`` text is output.
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] running command')
        cmd = " ".join(
            [
                shlex.quote(a.encode('unicode-escape').decode())
                for a in parsed_args.arg
            ]
        )
        if "help" not in cmd:
            self.app.secrets.requires_environment()
            self.app.secrets.read_secrets_and_descriptions()
        return call(cmd, shell=True)  # nosec


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
