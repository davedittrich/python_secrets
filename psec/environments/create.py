# -*- coding: utf-8 -*-

import argparse
import logging
import psec.secrets
import psec.utils
import textwrap


from cliff.command import Command


class EnvironmentsCreate(Command):
    """Create environment(s)."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        how = parser.add_mutually_exclusive_group(required=False)
        how.add_argument(
            '-A', '--alias',
            action='store',
            dest='alias',
            default=None,
            help="Environment to alias (default: None)"
        )
        how.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Environment directory to clone from (default: None)"
        )
        default_environment = psec.secrets.SecretsEnvironment().environment()
        parser.add_argument('env',
                            nargs='*',
                            default=[default_environment])
        parser.epilog = textwrap.dedent("""
            Empty environments can be created as needed, one at a time or
            several at once. Specify the names on the command line as arguments:

            .. code-block:: console

                $ psec environments create development testing production
                [+] environment directory /Users/dittrich/.secrets/development created
                [+] environment directory /Users/dittrich/.secrets/testing created
                [+] environment directory /Users/dittrich/.secrets/production created

            ..

            In some special circumstances, it may be necessary to have one set
            of identical secrets that have different environment names. If
            this happens, you can create an alias (see also the
            ``environments list`` command):

            .. code-block:: console

                $ psec environments create --alias evaluation testing

            ..

            To make it easier to bootstrap an open source project, where the
            use may not be intimately familiar with all necessary secrets
            and settings, you can make their life easier by preparing an
            empty set of secret descriptions that will help prompt the
            user to set them. You can do this following these steps:

            #. Create a template secrets environment directory that contains
               just the secrets definitions. This example uses the template
               found in the `davedittrich/goSecure`_ repository (directory
               https://github.com/davedittrich/goSecure/tree/master/secrets).

            #. Use this template to clone a secrets environment, which will
               initially be empty:

               .. code-block:: console

                   $ psec environments create test --clone-from ~/git/goSecure/secrets
                   [+] new password variable "gosecure_app_password" is not defined
                   [+] new string variable "gosecure_client_ssid" is not defined
                   [+] new string variable "gosecure_client_ssid" is not defined
                   [+] new string variable "gosecure_client_psk" is not defined
                   [+] new password variable "gosecure_pi_password" is not defined
                   [+] new string variable "gosecure_pi_pubkey" is not defined
                   [+] environment directory /Users/dittrich/.secrets/test created

               ..

            .. _davedittrich/goSecure: https://github.com/davedittrich/goSecure

            Note: Directory and file permissions on cloned environments will prevent
            ``other`` from having read/write/execute permissions (i.e., ``o-rwx`` in
            terms of the ``chmod`` command.)
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] creating environment(s)')
        if parsed_args.alias is not None:
            if len(parsed_args.env) != 1:
                raise RuntimeError(
                    '[-] --alias requires one source environment')
            se = psec.secrets.SecretsEnvironment(environment=parsed_args.alias)
            se.environment_create(source=parsed_args.env[0],
                                  alias=True)
            if se.environment_exists():
                self.LOG.info(
                    f"[+] environment '{parsed_args.alias}' aliased "
                    f"to '{parsed_args.env[0]}'")
            else:
                raise RuntimeError('[-] creating environment failed')
        else:
            # Default to app environment identifier
            if len(parsed_args.env) == 0:
                parsed_args.env = list(self.app.environment)
            for e in parsed_args.env:
                se = psec.secrets.SecretsEnvironment(environment=e)
                se.environment_create(source=parsed_args.clone_from)
                self.LOG.info(
                    f"[+] environment '{e}' ({se.environment_path()}) created")
                if parsed_args.clone_from:
                    se.read_secrets(from_descriptions=True)
                    se.write_secrets()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
