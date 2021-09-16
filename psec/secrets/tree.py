# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import textwrap

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment
from psec.utils import secrets_tree


class SecretsTree(Command):
    """Output tree listing of groups and secrets in environment."""

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            The ``secrets tree`` command produces output similar to the Unix
            ``tree`` command. This gives you a visual overview of the groupings
            of secrets in the target environment:

            .. code-block:: console

                $ psec secrets tree my_environment
                my_environment
                ├── myapp
                │   ├── myapp_app_password
                │   ├── myapp_client_psk
                │   ├── myapp_client_ssid
                │   ├── myapp_ondemand_wifi
                │   └── myapp_pi_password
                └── oauth
                    ├── google_oauth_client_id
                    ├── google_oauth_client_secret
                    ├── google_oauth_refresh_token
                    └── google_oauth_username

            ..
            """)
        return parser

    def take_action(self, parsed_args):
        self.logger.debug('[*] outputting secrets tree')
        environment = parsed_args.environment
        if environment is None:
            environment = self.app.options.environment
        e = SecretsEnvironment(environment=environment)
        e.requires_environment()
        e.read_secrets_and_descriptions()
        secrets_tree(e, outfile=sys.stdout)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
