# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from psec.secrets import SECRET_TYPES


class SecretsDescribe(Lister):
    """Describe supported secret types."""

    LOG = logging.getLogger(__name__)

    # Note: Not totally DRY. Replicates some logic from SecretsShow()

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            To get descriptions for a subset of secrets, specify their
            names as the arguments.

            If you instead want to get descriptions of all secrets in
            one or more groups, use the ``--group`` option and specify
            the group names as the arguments.
            """)

        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '-g', '--group',
            dest='args_group',
            action="store_true",
            default=False,
            help="Arguments are groups to list (default: False)"
        )
        what.add_argument(
            '-t', '--types',
            dest='types',
            action="store_true",
            default=False,
            help="Describe types (default: False)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('describing secrets')
        if parsed_args.types:
            columns = [k.title() for k in SECRET_TYPES[0].keys()]
            data = [[v for k, v in i.items()] for i in SECRET_TYPES]
        else:
            self.app.secrets.requires_environment()
            self.app.secrets.read_secrets_and_descriptions()
            variables = []
            if parsed_args.args_group:
                if not len(parsed_args.arg):
                    raise RuntimeError('No group specified')
                for g in parsed_args.arg:
                    try:
                        variables.extend(
                            [v for v
                                in self.app.secrets.get_items_from_group(g)]
                        )
                    except KeyError as e:
                        raise RuntimeError('Group {} '.format(str(e)) +
                                           'does not exist')
            else:
                variables = parsed_args.arg \
                    if len(parsed_args.arg) > 0 \
                    else [k for k, v in self.app.secrets.items()]
            columns = ('Variable', 'Type', 'Prompt')
            data = (
                    [(k,
                      self.app.secrets.get_secret_type(k),
                      self.app.secrets.get_prompt(k))
                        for k, v in self.app.secrets.items()
                        if k in variables]
            )
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
