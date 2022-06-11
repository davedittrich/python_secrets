# -*- coding: utf-8 -*-

"""
Create environment(s).
"""

import logging

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment
from psec.utils import get_default_environment


class EnvironmentsCreate(Command):
    """
    Create environment(s).

    Empty environments can be created as needed, one at a time or several at
    once. Specify the names on the command line as arguments::

        $ psec environments create development testing production
        [+] environment directory /Users/dittrich/.secrets/development created
        [+] environment directory /Users/dittrich/.secrets/testing created
        [+] environment directory /Users/dittrich/.secrets/production created

    In some special circumstances, it may be necessary to have one set of
    identical secrets that have different environment names. If this happens,
    you can create an alias (see also the ``environments list`` command)::

        $ psec environments create --alias evaluation testing

    To make it easier to bootstrap an open source project, where the use may
    not be intimately familiar with all necessary secrets and settings, you can
    make their life easier by preparing an empty set of secret descriptions
    that will help prompt the user to set them. You can do this following these
    steps:

    #. Create a template secrets environment directory that contains
       just the secrets definitions. This example uses the template
       found in the `davedittrich/goSecure`_ repository (directory
       https://github.com/davedittrich/goSecure/tree/master/secrets).

    #. Use this template to clone a secrets environment, which will
       initially be empty::

           $ psec environments create test --clone-from ~/git/goSecure/secrets
           [+] new password variable "gosecure_app_password" is unset
           [+] new string variable "gosecure_client_ssid" is unset
           [+] new string variable "gosecure_client_ssid" is unset
           [+] new string variable "gosecure_client_psk" is unset
           [+] new password variable "gosecure_pi_password" is unset
           [+] new string variable "gosecure_pi_pubkey" is unset
           [+] environment directory /Users/dittrich/.secrets/test created

    .. _davedittrich/goSecure: https://github.com/davedittrich/goSecure

    Note: Directory and file permissions on cloned environments will prevent
    ``other`` from having read/write/execute permissions (i.e., ``o-rwx`` in
    terms of the ``chmod`` command.)
    """

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        how = parser.add_mutually_exclusive_group(required=False)
        default_environment = get_default_environment()
        how.add_argument(
            '-A', '--alias',
            action='store',
            dest='alias',
            default=None,
            help='Environment to alias'
        )
        how.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help='Environment directory to clone from'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Create secrets base directory'
        )
        parser.add_argument(
            'env',
            nargs='*',
            default=[default_environment]
        )
        return parser

    def take_action(self, parsed_args):
        secrets_basedir = self.app.secrets_basedir
        if parsed_args.alias is not None:
            if len(parsed_args.env) != 1:
                raise RuntimeError(
                    '[-] --alias requires one source environment')
            se = SecretsEnvironment(
                environment=parsed_args.alias,
                secrets_basedir=secrets_basedir,
                create_root=parsed_args.force,
            )
            se.environment_create(
                source=parsed_args.env[0],
                alias=True
            )
            if se.environment_exists():
                self.logger.info(
                    "[+] environment '%s' aliased to '%s'",
                    parsed_args.alias,
                    parsed_args.env[0]
                )
            else:
                raise RuntimeError('[-] creating environment failed')
        else:
            # Default to app environment identifier
            if len(parsed_args.env) == 0:
                parsed_args.env = list(self.app.environment)
            for environment in parsed_args.env:
                se = SecretsEnvironment(
                    environment=environment,
                    secrets_basedir=secrets_basedir,
                    create_root=True,
                )
                se.environment_create(source=parsed_args.clone_from)
                self.logger.info(
                    "[+] environment '%s' created (%s)",
                    environment,
                    se.get_environment_path()
                )
                if parsed_args.clone_from:
                    se.read_secrets(from_descriptions=True)
                    se.write_secrets()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
