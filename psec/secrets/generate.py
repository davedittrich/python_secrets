# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from psec.secrets import generate_secret
from psec.secrets import natural_number
from psec.secrets import DELIMITER
from psec.secrets import MAX_WORDS_LENGTH
from psec.secrets import MIN_WORDS_LENGTH
from psec.secrets import MAX_ACROSTIC_LENGTH
from psec.secrets import MIN_ACROSTIC_LENGTH
from xkcdpass.xkcd_password import CASE_METHODS


class SecretsGenerate(Command):
    """Generate values for secrets."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--min-words-length',
            action='store',
            type=natural_number,
            dest='min_words_length',
            default=MIN_WORDS_LENGTH,
            help='Minimum word length for XKCD words list ' +
                 '(default: {})'.format(MIN_WORDS_LENGTH)
        )
        parser.add_argument(
            '--max-words-length',
            action='store',
            type=natural_number,
            dest='max_words_length',
            default=MAX_WORDS_LENGTH,
            help='Maximum word length for XKCD words list ' +
                 '(default: {})'.format(MIN_WORDS_LENGTH)
        )
        parser.add_argument(
            '--min-acrostic-length',
            action='store',
            type=natural_number,
            dest='min_acrostic_length',
            default=MIN_ACROSTIC_LENGTH,
            help='Minimum length of acrostic word for XKCD password' +
                 '(default: {})'.format(MIN_ACROSTIC_LENGTH)
        )
        parser.add_argument(
            '--max-acrostic-length',
            action='store',
            type=natural_number,
            dest='max_acrostic_length',
            default=MAX_ACROSTIC_LENGTH,
            help='Maximum length of acrostic word for XKCD password' +
                 '(default: {})'.format(MAX_ACROSTIC_LENGTH)
        )
        parser.add_argument(
            '--acrostic',
            action='store',
            dest='acrostic',
            default=None,
            help='Acrostic word for XKCD password ' +
                 '(default: None)'
        )
        parser.add_argument(
            '--delimiter',
            action='store',
            dest='delimiter',
            default=DELIMITER,
            help='Delimiter for XKCD password ' +
                 '(default: "{}")'.format(DELIMITER)
        )
        parser.add_argument(
            "-C", "--case",
            dest="case",
            type=str,
            metavar="CASE",
            choices=list(CASE_METHODS.keys()), default="alternating",
            help=(
                "Choose the method for setting the case of each word "
                "in the passphrase. "
                "Choices: {cap_meths} (default: 'lower').".format(
                    cap_meths=list(CASE_METHODS.keys())
                )))
        parser.add_argument(
            '-U', '--unique',
            action='store_true',
            dest='unique',
            default=False,
            help="Generate unique values for each " +
            "type of secret (default: False)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            To generate a subset of generable secrets, specify them
            as the arguments to this command. If no secrets are specified,
            all generable secrets are (re)generated.
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] generating secrets')
        self.app.secrets.read_secrets_and_descriptions()
        # If no secrets specified, default to all secrets
        to_change = parsed_args.arg \
            if len(parsed_args.arg) > 0 \
            else [k for k, v in self.app.secrets.items()]
        for secret in to_change:
            secret_type = self.app.secrets.get_secret_type(secret)
            if secret_type is None:
                raise TypeError(
                    f"[-] secret '{secret}' "
                    "has no type definition")
            arguments = self.app.secrets.get_secret_arguments(secret)
            value = generate_secret(secret_type=secret_type,
                                    *arguments,
                                    **dict(parsed_args._get_kwargs()))
            if value is not None:
                self.LOG.debug(
                    f"[+] generated {secret_type} for {secret}")
                self.app.secrets.set_secret(secret, value)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
