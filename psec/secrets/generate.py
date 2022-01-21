# -*- coding: utf-8 -*-

"""
Generate values for secrets.
"""

import logging

from cliff.command import Command
from xkcdpass.xkcd_password import CASE_METHODS

from psec.secrets_environment import (
    generate_secret,
    DELIMITER,
    MAX_WORDS_LENGTH,
    MIN_WORDS_LENGTH,
    MAX_ACROSTIC_LENGTH,
    MIN_ACROSTIC_LENGTH,
)
from psec.utils import natural_number


class SecretsGenerate(Command):
    """
    Generate values for secrets.

    Sets variables by generating values according to the ``Type`` definition
    for each variable.

    If you include the ``--from-options`` flag, string variables will also be
    set according to their default value as described in the help output for
    the ``secrets set`` command. This allows as many variables as possible to
    be set with a single command (rather than requiring the user to do both
    ``secrets set`` and ``secrets generate`` as two separate steps.

    To affect only a subset of secrets, specify their names as the arguments to
    this command. If no secrets are specified, all secrets will be affected.
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--from-options',
            action='store_true',
            dest='from_options',
            default=False,
            help='Set variables from first available option'
        )
        parser.add_argument(
            '--min-words-length',
            action='store',
            type=natural_number,
            dest='min_words_length',
            default=MIN_WORDS_LENGTH,
            help='Minimum word length for XKCD words list'
        )
        parser.add_argument(
            '--max-words-length',
            action='store',
            type=natural_number,
            dest='max_words_length',
            default=MAX_WORDS_LENGTH,
            help='Maximum word length for XKCD words list'
        )
        parser.add_argument(
            '--min-acrostic-length',
            action='store',
            type=natural_number,
            dest='min_acrostic_length',
            default=MIN_ACROSTIC_LENGTH,
            help='Minimum length of acrostic word for XKCD password'
        )
        parser.add_argument(
            '--max-acrostic-length',
            action='store',
            type=natural_number,
            dest='max_acrostic_length',
            default=MAX_ACROSTIC_LENGTH,
            help='Maximum length of acrostic word for XKCD password'
        )
        parser.add_argument(
            '--acrostic',
            action='store',
            dest='acrostic',
            default=None,
            help='Acrostic word for XKCD password'
        )
        parser.add_argument(
            '--delimiter',
            action='store',
            dest='delimiter',
            default=DELIMITER,
            help='Delimiter for XKCD password'
        )
        parser.add_argument(
            "-C", "--case",
            dest="case",
            type=str,
            metavar="CASE",
            choices=list(CASE_METHODS.keys()), default="alternating",
            help=(
                'Choose the method for setting the case of each '
                'word in the passphrase. '
                f"Choices: {list(CASE_METHODS.keys())}"
            )
        )
        parser.add_argument(
            '-U', '--unique',
            action='store_true',
            dest='unique',
            default=False,
            help='Generate unique values for each type of secret'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        self.logger.debug('[*] generating secrets')
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_and_descriptions()
        # If no secrets specified, default to all secrets
        to_change = parsed_args.arg \
            if len(parsed_args.arg) > 0 \
            else [k for k, v in se.items()]
        for secret in to_change:
            secret_type = se.get_secret_type(secret)
            # >> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'string'  # noqa
            # Severity: Low   Confidence: Medium
            # Location: psec/secrets/generate.py:142
            # More Info: https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html  # noqa
            # 142                 if parsed_args.from_options and secret_type == 'string':  # noqa
            if secret_type is None:
                raise TypeError(
                    f"[-] secret '{secret}' "
                    "has no type definition")
            arguments = se.get_secret_arguments(secret)
            default_value = se.get_default_value(secret)
            if parsed_args.from_options and default_value:
                value = default_value
            else:
                value = generate_secret(
                    secret_type=secret_type,
                    *arguments,
                    **dict(parsed_args._get_kwargs())
                )
            if value is not None:
                self.logger.debug(
                    "[+] generated %s for %s", secret_type, secret)
                se.set_secret(secret, value)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
