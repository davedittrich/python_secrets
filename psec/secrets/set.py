# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec
import textwrap

from cliff.command import Command
from psec.secrets import BOOLEAN_OPTIONS
from psec.secrets import is_generable
from psec.secrets import SecretsEnvironment
from subprocess import run, PIPE  # nosec


class SecretsSet(Command):
    """Set values manually for secrets."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--undefined',
            action='store_true',
            dest='undefined',
            default=False,
            help="Set values for undefined variables (default: False)"
        )
        how = parser.add_mutually_exclusive_group(required=False)
        how.add_argument(
            '--from-environment',
            metavar='<environment>',
            dest='from_environment',
            default=None,
            help="Environment from which to copy " +
                 "secret value(s) (default: None)"
        )
        how.add_argument(
            '--from-options',
            action='store_true',
            dest='from_options',
            default=False,
            help="Set from first available option (default: False)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            One or more secrets can be set directly by specifying them
            as ``variable=value`` pairs as the arguments to this command.

            .. code-block:: console

                $ psec secrets set trident_db_pass="rural coffee purple sedan"

            ..

            If no secrets as specified, you will be prompted for each
            secrets.

            Adding the ``--undefined`` flag will limit the secrets being set
            to only those that are currently not set.  If values are not set,
            you are prompted for the value.

            When cloning an environment from definitions in a source repository
            or an existing environment, you can set secrets by copying them
            from another existing environment using the ``--from-environment``
            option.

            .. code-block:: console

                $ psec secrets set gosecure_pi_password --from-environment goSecure

            ..

            When you are doing this immediately after cloning (when all variables
            are undefined) you can set all undefined variables at once from
            another environment this way:

            .. code-block:: console

                $ psec environments create --clone-from goSecure
                $ psec secrets set --undefined --from-environment goSecure

            ..

            To facilitate setting variables from another environment where the
            variable names may differ, use the assignment style syntax for
            arguments along with the ``--from-environment`` option, like this:

            .. code-block:: console

                $ psec secrets set hypriot_client_psk=gosecure_client_psk \\
                > hypriot_client_ssid=gosecure_client_ssid \\
                > --from-environment goSecure

            ..

            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] setting secrets')
        if (
            len(parsed_args.arg) == 0
            and not parsed_args.undefined
            and not parsed_args.from_options
        ):
            raise RuntimeError('[-] no secrets specified to be set')
        se = self.app.secrets
        se.read_secrets_and_descriptions()
        options = dict(se.Options)
        # TODO(dittrich): Use Variable map like this elsewhere
        variables = dict(se.Variable)
        types = dict(se.Type)
        from_env = None
        if parsed_args.from_environment is not None:
            from_env = SecretsEnvironment(
                environment=parsed_args.from_environment)
            from_env.read_secrets()
            options = dict(from_env.secrets.Options)
            variables = dict(from_env.secrets.Variable)
            types = dict(from_env.secrets.Type)
        args = (
            list(variables.keys()) if not len(parsed_args.arg)
            else parsed_args.arg
        )
        if parsed_args.undefined:
            # Downselect to just those currently undefined
            args = [k for k, v in variables
                    if v in [None, '']]
        if not len(args):
            raise RuntimeError('[-] no secrets identified to be set')
        for arg in args:
            k, v, k_type = None, None, None
            if parsed_args.from_options:
                k, v, k_type = (
                    arg,
                    options.get(arg, '').split(',')[0],
                    types.get(arg)
                )
                # Don't set from options if the type is generable
                if is_generable(k_type):
                    continue
                v = None if v == '*' else v
            elif '=' not in arg:
                # No value was specified with the argument
                k = arg
                k_type = self.app.secrets.get_type(k)
                if k_type is None:
                    self.LOG.info(f"[-] no description for '{k}'")
                    raise RuntimeError(
                        f"[-] variable '{k}' has no description")
                if from_env is not None:
                    # Getting value from same var, different environment
                    v = from_env.get_secret(k, allow_none=True)
                else:
                    # Try to prompt user for value
                    if (k_type == 'boolean' and
                            k not in self.app.secrets.Options):
                        # Default options for boolean type
                        self.app.secrets.Options[k] = BOOLEAN_OPTIONS
                    if k in self.app.secrets.Options:
                        # Attempt to select from list of option dictionaries
                        v = psec.utils.prompt_options_dict(
                            options=self.app.secrets.Options[k],
                            prompt=self.app.secrets.get_prompt(k)
                            )
                    else:
                        # Just ask user for value
                        v = psec.utils.prompt_string(
                            prompt=self.app.secrets.get_prompt(k),
                            default=("" if v is None else v)
                            )
            else:  # ('=' in arg)
                # Assignment syntax found (a=b)
                lhs, rhs = arg.split('=')
                k_type = self.app.secrets.get_type(lhs)
                if k_type is None:
                    self.LOG.info(f"[-] no description for '{lhs}'")
                    raise RuntimeError(
                        f"[-] variable '{lhs}' has no description")
                k = lhs
                if from_env is not None:
                    # Get value from different var in different environment
                    v = from_env.get_secret(rhs, allow_none=True)
                    self.LOG.info(
                        f"[+] getting value from '{rhs}' in "
                        f"environment '{str(from_env)}'")
                else:
                    # Value was specified in arg
                    v = rhs
                if v is not None:
                    # Is the value indirectly referenced?
                    if v.startswith('@'):
                        if v[1] == '~':
                            _path = os.path.expanduser(v[1:])
                        else:
                            _path = v[1:]
                        with open(_path, 'r') as f:
                            v = f.read().strip()
                    elif v.startswith('!'):
                        # >> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.  # noqa
                        #    Severity: Low   Confidence: High
                        #    Location: psec/secrets.py:641
                        p = run(v[1:].split(),
                                stdout=PIPE,
                                stderr=PIPE,
                                shell=False)
                        v = p.stdout.decode('UTF-8').strip()
            # After all that, did we get a value?
            if v is None:
                self.LOG.info(f"[-] could not obtain value for '{k}'")
            else:
                self.LOG.debug(f"[+] setting variable '{k}'")
                self.app.secrets.set_secret(k, v)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
