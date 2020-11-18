# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.command import Command


class SecretsGet(Command):
    """Get value associated with a secret."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-C', '--content',
            action='store_true',
            dest='content',
            default=False,
            help="Get content if secret is a file path " +
            "(default: False)"
        )
        parser.add_argument('secret', nargs='?', default=None)
        parser.epilog = textwrap.dedent("""
            To get a subset of secrets, specify them as arguments to this
            command. If no secrets are specified, they are all returned.
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] get secret')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        if parsed_args.secret is not None:
            value = self.app.secrets.get_secret(
                parsed_args.secret, allow_none=True)
            if not parsed_args.content:
                print(value)
            else:
                if os.path.exists(value):
                    with open(value, 'r') as f:
                        content = f.read().replace('\n', '')
                    print(content)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
