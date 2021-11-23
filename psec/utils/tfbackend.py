# -*- coding: utf-8 -*-


import argparse
import logging
import os
import textwrap

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment


class TfBackend(Command):
    """
    Enable Terraform backend support to move terraform.tfstate file
    out of current working directory into environment path.
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--path',
            action='store_true',
            dest='path',
            default=False,
            help="Print path and exit (default: False)"
        )
        # tfstate = None
        # try:
        #     tfstate = os.path.join(self.app.secrets.environment_path(),
        #                            "terraform.tfstate")
        # except AttributeError:
        #     pass
        parser.epilog = textwrap.dedent("""
            TBD(dittrich): Write this...
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        e = SecretsEnvironment(environment=self.app.options.environment)
        tmpdir = e.tmpdir_path()
        backend_file = os.path.join(os.getcwd(), 'tfbackend.tf')
        tfstate_file = os.path.join(tmpdir, 'terraform.tfstate')
        backend_text = textwrap.dedent("""\
            terraform {{
              backend "local" {{
              path = "{tfstate_file}"
              }}
            }}
            """.format(tfstate_file=tfstate_file))

        if parsed_args.path:
            self.logger.debug('[+] showing terraform state file path')
            print(tfstate_file)
        else:
            self.logger.debug('[+] setting up terraform backend')
            if os.path.exists(backend_file):
                self.logger.debug("[+] updating '%s'", backend_file)
            else:
                self.logger.debug("[+] creating '%s'", backend_file)
            with open(backend_file, 'w') as f:
                f.write(backend_text)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
