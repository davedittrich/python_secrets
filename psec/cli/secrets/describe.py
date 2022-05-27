# -*- coding: utf-8 -*-

"""
Describe supported secret types.
"""

import logging

from cliff.lister import Lister
from psec.secrets_environment import SECRET_TYPES


class SecretsDescribe(Lister):
    """
    Describe supported secret types.

    To get descriptions for a subset of secrets, specify their names as the
    arguments::

        $ psec secrets describe jenkins_admin_password
        +------------------------+---------+----------+--------------------------------------+---------+
        | Variable               | Group   | Type     | Prompt                               | Options |
        +------------------------+---------+----------+--------------------------------------+---------+
        | jenkins_admin_password | jenkins | password | Password for Jenkins 'admin' account | *       |
        +------------------------+---------+----------+--------------------------------------+---------+

    If you instead want to get descriptions of all secrets in one or more
    groups, use the ``--group`` option and specify the group names as the
    arguments.

    To instead see the values and exported environment variables associated
    with secrets, use the ``secrets show`` command instead.
    """  # noqa

    logger = logging.getLogger(__name__)

    # Note: Not totally DRY. Replicates some logic from SecretsShow()

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--undefined',
            action='store_true',
            dest='undefined',
            default=False,
            help='Only show variables that are not yet defined'
        )
        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '-g', '--group',
            dest='args_group',
            action="store_true",
            default=False,
            help='Arguments are groups to list'
        )
        what.add_argument(
            '-t', '--types',
            dest='types',
            action="store_true",
            default=False,
            help='Describe types'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        if parsed_args.types:
            columns = [k.title() for k in SECRET_TYPES[0].keys()]
            data = [[v for k, v in i.items()] for i in SECRET_TYPES]
        else:
            se.requires_environment()
            se.read_secrets_and_descriptions()
            variables = []
            if parsed_args.args_group:
                if len(parsed_args.arg) == 0:
                    raise RuntimeError('[-] no group specified')
                for g in parsed_args.arg:
                    try:
                        variables.extend([
                            v for v
                            in se.get_items_from_group(g)
                        ])
                    except KeyError as e:
                        raise RuntimeError(
                            f"[-] group {str(e)} does not exist"
                        )
            else:
                variables = parsed_args.arg \
                    if len(parsed_args.arg) > 0 \
                    else [k for k, v in se.items()]
            columns = (
                'Variable', 'Group', 'Type', 'Prompt', 'Options', 'Help'
            )
            data = (
                [
                    (
                        k,
                        se.get_group(k),
                        se.get_secret_type(k),
                        se.get_prompt(k),
                        se.get_options(k),
                        se.get_help(k)
                    )
                    for k, v in se.items()
                    if (k in variables and
                        (not parsed_args.undefined or
                         (parsed_args.undefined and v in [None, ''])))
                ]
            )
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
