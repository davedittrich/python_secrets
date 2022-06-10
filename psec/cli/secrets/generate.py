# -*- coding: utf-8 -*-

"""
Generate values for secrets.
"""

import logging

from cliff.command import Command

# Register handlers to ensure parser arguments are available.
# FIXME: Doing this to enable 'make docs' to work properly.
from psec.secrets_environment.factory import SecretFactory
from psec.secrets_environment.handlers import *  # noqa


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
            '-U', '--unique',
            action='store_true',
            dest='unique',
            default=False,
            help='Generate unique values for each type of secret'
        )
        try:
            secret_factory = self.app.secret_factory
        except AttributeError:
            secret_factory = SecretFactory()
        # FIXME: Cliff automatic document generation fails here.
        parser = secret_factory.add_parser_arguments(parser)
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_and_descriptions()
        # If no secrets specified, default to all secrets
        to_change = parsed_args.arg \
            if len(parsed_args.arg) > 0 \
            else [k for k, v in se.items()]
        cached_result = {}
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
            default_value = se.get_default_value(secret)
            if parsed_args.from_options and default_value:
                value = default_value
            else:
                handler = self.app.secret_factory.get_handler(secret_type)
                value = cached_result.get(
                    secret_type,
                    handler.generate_secret(
                        **dict(parsed_args._get_kwargs())
                    )
                )
                if not parsed_args.unique and handler.is_generable():
                    cached_result[secret_type] = value
            if value is not None:
                self.logger.debug(
                    "[+] generated %s for %s", secret_type, secret)
                se.set_secret(secret, value)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
