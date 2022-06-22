# -*- coding: utf-8 -*-

"""
Set values manually for secrets.
"""

import logging
import os

from subprocess import run, PIPE  # nosec
from cliff.command import Command

from psec.secrets_environment import (
    BOOLEAN_OPTIONS,
    SecretsEnvironment,
    is_generable,
)
from psec.utils import (
    prompt_options_list,
    prompt_string,
)


class SecretsSet(Command):
    """
    Set values manually for secrets.

    One or more secrets can be set directly by specifying them as
    ``variable=value`` pairs as the arguments to this command::

        $ psec secrets set trident_db_pass="rural coffee purple sedan"

    Adding the ``--undefined`` flag will limit the secrets being set to only
    those that are currently not set.  If values are not set, you are prompted
    for the value.

    When cloning an environment from definitions in a source repository or an
    existing environment, you can set secrets by copying them from another
    existing environment using the ``--from-environment`` option::

        $ psec secrets set gosecure_pi_password --from-environment goSecure

    When you are doing this immediately after cloning (when all variables
    are undefined) you can set all undefined variables at once from
    another environment this way::

        $ psec environments create --clone-from goSecure
        $ psec secrets set --undefined --from-environment goSecure

    To facilitate setting variables from another environment where the variable
    names may differ, use the assignment style syntax for arguments along with
    the ``--from-environment`` option, like this::

        $ psec secrets set hypriot_client_psk=gosecure_client_psk \\
        > hypriot_client_ssid=gosecure_client_ssid \\
        > --from-environment goSecure

    If you do not provide values for variables using assignment syntax and you
    are not copying values from another environment, you will be prompted for
    values according to how the options field is defined.

    * If the *only* option is ``*`` (meaning "any string"), you will be
      prompted to enter a value. When prompted this way, you can cancel setting
      the variable by entering an empty string. If you really want the value to
      be an empty string, you *must* use the assignment syntax with an empty
      string like this: ``variable=''``

    * An options list that *does not contain* a ``*`` defines a finite set of
      options. This means you are resticted to *only* choosing from the list.
      This is similar to the ``Boolean`` type, which can only have a value of
      ``true`` or ``false``.

    * If one or more options are listed *along with* ``*``, you can either
      choose from one of the listed values or select ``*`` to manually enter a
      value not in the list.

    * You can back out of making a change by selecting ``<CANCEL>`` from
      the list.
    """  # noqa

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--undefined',
            action='store_true',
            dest='undefined',
            default=False,
            help='Set values for undefined variables'
        )
        parser.add_argument(
            '--ignore-missing',
            action='store_true',
            dest='ignore_missing',
            default=False,
            help='Skip setting variables that are not defined'
        )
        how = parser.add_mutually_exclusive_group(required=False)
        how.add_argument(
            '--from-environment',
            metavar='<environment>',
            dest='from_environment',
            default=None,
            help='Environment from which to copy secret value(s)'
        )
        how.add_argument(
            '--from-options',
            action='store_true',
            dest='from_options',
            default=False,
            help='Set from first available option'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        if (
            len(parsed_args.arg) == 0
            and not parsed_args.undefined
            and not parsed_args.from_options
        ):
            raise RuntimeError('[-] no secrets specified to be set')
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_and_descriptions()
        # TODO(dittrich): Use Variable map like this elsewhere
        variables = dict(se.Variable)
        types = dict(se.Type)
        from_env = None
        if parsed_args.from_environment is not None:
            from_env = SecretsEnvironment(
                environment=parsed_args.from_environment)
            from_env.read_secrets()
            variables = dict(from_env.Variable)
            types = dict(from_env.Type)
        args = (
            list(variables.keys()) if len(parsed_args.arg) == 0
            else parsed_args.arg
        )
        if parsed_args.undefined and len(variables) > 0:
            # Downselect to just those currently undefined
            args = [
                k for k, v in variables.items()
                if v in [None, '']
            ]
        if len(args) == 0:
            raise RuntimeError('[-] no secrets identified to be set')
        for arg in args:
            k, v, k_type = None, None, None
            if parsed_args.from_options:
                k, v, k_type = (
                    arg,
                    se.get_default_value(arg),
                    types.get(arg)
                )
                # Don't set from options if the type is generable
                if is_generable(k_type):
                    continue
            elif '=' not in arg:
                # No value was specified with the argument
                k = arg
                k_type = se.get_type(k)
                if k_type is None:
                    if parsed_args.ignore_missing:
                        continue
                    raise RuntimeError(
                        f"[-] variable '{k}' has no description")
                if from_env is not None:
                    # Getting value from same var, different environment
                    v = from_env.get_secret(k, allow_none=True)
                else:
                    # Try to prompt user for value
                    if (
                        k_type == 'boolean'
                        and k not in se.Options
                    ):
                        # Default options for boolean type
                        se.Options[k] = BOOLEAN_OPTIONS
                    k_options = se.get_options(k)
                    if (
                        k_options != '*'
                        and k in se.Options
                    ):
                        # Attempt to select from list. Options will look like
                        # 'a,b' or 'a,b,*', or 'a,*'.
                        old_v = se.get_secret(k, allow_none=True)
                        v = prompt_options_list(
                            options=k_options.split(','),
                            default=(None if old_v in ['', None] else old_v),
                            prompt=se.get_prompt(k)
                        )
                        if v is None:
                            # User cancelled selection.
                            break
                        v = v if v not in ['', '*'] else None
                    # Ask user for value
                    if v is None:
                        v = prompt_string(
                            prompt=se.get_prompt(k),
                            default=""
                        )
                    v = v if v != '' else None
            else:  # ('=' in arg)
                # Assignment syntax found (a=b)
                lhs, rhs = arg.split('=')
                k_type = se.get_type(lhs)
                if k_type is None:
                    if parsed_args.ignore_missing:
                        continue
                    raise RuntimeError(
                        f"[-] variable '{lhs}' has no description")
                k = lhs
                if from_env is not None:
                    # Get value from different var in different environment
                    v = from_env.get_secret(rhs, allow_none=True)
                    self.logger.info(
                        "[+] getting value from '%s' in environment '%s'",
                        rhs,
                        str(from_env)
                    )
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
                self.logger.info("[-] could not obtain value for '%s'", k)
            else:
                self.logger.debug("[+] setting variable '%s'", k)
                se.set_secret(k, v)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
