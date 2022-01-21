# -*- coding: utf-8 -*-

"""
Get value associated with a secret.
"""

import logging
import os

from cliff.command import Command


class SecretsGet(Command):
    """
    Get value associated with a secret.

    To get a subset of secrets, specify them as arguments to this
    command. If no secrets are specified, they are all returned.
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '-C', '--content',
            action='store_true',
            dest='content',
            default=False,
            help='Get content if secret is a file path'
        )
        parser.add_argument(
            'secret',
            nargs='?',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_and_descriptions()
        if parsed_args.secret is not None:
            value = se.get_secret(
                parsed_args.secret, allow_none=True)
            if not parsed_args.content:
                print(value)
            else:
                if os.path.exists(value):
                    with open(value, 'r') as f:
                        content = f.read().replace('\n', '')
                    print(content)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
