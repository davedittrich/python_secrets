# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec
import textwrap

from cliff.lister import Lister


class SecretsShow(Lister):
    """List the contents of the secrets file or definitions."""

    LOG = logging.getLogger(__name__)

    # Note: Not totally DRY. Replicates some logic from SecretsDescribe()

    def get_parser(self, prog_name):
        # Sorry for the double-negative, but it works better
        # this way for the user as a flag and to have a default
        # of redacting (so they need to turn it off)
        redact = not (os.getenv('D2_NO_REDACT', "FALSE").upper()
                      in ["true".upper(), "1", "yes".upper()])

        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-C', '--no-redact',
            action='store_false',
            dest='redact',
            default=redact,
            help="Do not redact values in output (default: {})".format(redact)
        )
        parser.add_argument(
            '-p', '--prompts',
            dest='args_prompts',
            action="store_true",
            default=False,
            help="Include prompts (default: False)"
        )
        parser.add_argument(
            '--undefined',
            action='store_true',
            dest='undefined',
            default=False,
            help="Only show variables that are not yet " +
                 "defined (default: False)"
        )
        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '-g', '--group',
            dest='args_group',
            action="store_true",
            default=False,
            help="Arguments are groups to show (default: False)"
        )
        what.add_argument(
            '-t', '--type',
            dest='args_type',
            action="store_true",
            default=False,
            help="Arguments are types to show (default: False)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""\
            The ``secrets show`` command is used to see variables, their
            values, and exported environment variables to help in using them
            in your code, shell scripts, etc. To see more metadata-ish information,
            such as their group, type, etc., use the ``secrets describe``
            command instead.

            To get show a subset of secrets, specify their names as arguments.
            If you instead want to show all secrets in one or more groups,
            use the ``--group`` option and specify the group names as arguments,
            or to show all secrets of one or more types, use the ``--type`` option.

            .. code-block:: console

                $ psec secrets show
                +------------------------+----------+------------------------+
                | Variable               | Value    | Export                 |
                +------------------------+----------+------------------------+
                | jenkins_admin_password | REDACTED | jenkins_admin_password |
                | myapp_app_password     | REDACTED | DEMO_app_password      |
                | myapp_client_psk       | REDACTED | DEMO_client_ssid       |
                | myapp_client_ssid      | REDACTED | DEMO_client_ssid       |
                | myapp_pi_password      | REDACTED | DEMO_pi_password       |
                | trident_db_pass        | REDACTED | trident_db_pass        |
                | trident_sysadmin_pass  | REDACTED | trident_sysadmin_pass  |
                +------------------------+----------+------------------------+

            Visually finding undefined variables in a very long list can be difficult.
            You can show just undefined variables with the ``--undefined`` option.
            ..
            """)  # noqa

        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] showing secrets')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        variables = []
        all_items = [k for k, v in self.app.secrets.items()]
        if parsed_args.args_group:
            if not len(parsed_args.arg):
                raise RuntimeError('[-] no group(s) specified')
            for g in parsed_args.arg:
                try:
                    variables.extend(
                        [v for v
                         in self.app.secrets.get_items_from_group(g)]
                    )
                except KeyError as e:
                    raise RuntimeError(
                        f"[-] group '{str(e)}' does not exist")
        elif parsed_args.args_type:
            if not len(parsed_args.arg):
                raise RuntimeError('[-] no type(s) specified')
            variables = [
                k for k, v
                in self.app.secrets.Type.items()
                if v in parsed_args.arg
            ]
        else:
            for v in parsed_args.arg:
                if v not in all_items:
                    # Validate requested variables exist.
                    raise RuntimeError(
                        f"[-] '{v}' is not defined in this environment")
            variables = parsed_args.arg \
                if len(parsed_args.arg) > 0 \
                else [k for k, v in self.app.secrets.items()]
        columns = ('Variable', 'Value', 'Export')
        data = ([(k,
                  psec.utils.redact(v, parsed_args.redact),
                  self.app.secrets.get_secret_export(k))
                for k, v in self.app.secrets.items()
                if (k in variables and
                    (not parsed_args.undefined or
                     (parsed_args.undefined and v in [None, ''])))])
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
