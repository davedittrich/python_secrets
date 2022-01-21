# -*- coding: utf-8 -*-

"""
Run a command line as a sub-shell.
"""

import logging
import shlex
from subprocess import call  # nosec

from cliff.command import Command

# NOTE: Calling subprocess.call() with shell=True can have security
# implications. To prevent user-supplied data from injecting commands
# into shell command lines, pass arguments as a list and ensure they
# are properly quoted.


class Run(Command):
    """
    Run a command line as a sub-shell.

    The ``run`` subcommand is used to run a command line in a sub-shell similar
    to using ``bash -c``.

    When used with the ``--elapsed`` option, you get more readable elapsed time
    information than with the ``time`` command::

        $ psec --elapsed run sleep 3
        [+] elapsed time 00:00:03.01

    When combined with the ``-E`` option to export a ``psec`` environment's
    secrets and variables into the process environment, the command sub-shell
    (and every shell that is subsequently forked & exec'd) will inherit these
    environment variables. Programs like Ansible and Terraform can then access
    the values by reference rather than requiring hard-coding values or passing
    values on the command line. You can even run a shell program like ``bash``
    or ``byobu`` in a nested shell to change default values for interactive
    sessions.

    Secrets and variables may be exported with their name, or may have an
    additional environment variable name (for programs that expect a particular
    prefix, like ``TF_`` for Terraform variables) as seen here::

        $ psec secrets show myapp_pi_password --no-redact
        +-------------------+---------------------------+------------------+
        | Variable          | Value                     | Export           |
        +-------------------+---------------------------+------------------+
        | myapp_pi_password | GAINS.ranged.ENGULF.wound | DEMO_pi_password |
        +-------------------+---------------------------+------------------+

    Without the ``-E`` option the export variable is not set::

        $ psec run -- bash -c 'env | grep DEMO_pi_password'
        $ psec run -- bash -c 'echo The demo password is ${DEMO_pi_password:-not set}'
        The demo password is not set

    With the ``-E`` option it is set and the sub-shell can expand it::

        $ psec -E run -- bash -c 'env | grep DEMO_pi_password'
        DEMO_pi_password=GAINS.ranged.ENGULF.wound
        $ psec run -- bash -c 'echo The demo password is ${DEMO_pi_password:-not set}'
        The demo password is GAINS.ranged.ENGULF.wound

    NOTE: The ``--`` you see in these examples is necessary to ensure that
    command line parsing by the shell to construct the argument vector for
    passing to the ``psec`` program is stopped so that the options meant for
    the sub-command are passed to it properly for parsing. Failing to add the
    ``--`` may result in a strange parsing error message, or unexpected
    behavior when the command line you typed is not parsed the way you assumed
    it would be::

        $ psec run bash -c 'env | grep DEMO_pi_password'
        usage: psec run [-h] [arg [arg ...]]
        psec run: error: unrecognized arguments: -c env | grep DEMO_pi_password

    You may use ``--elapsed`` without an environment if you do not need to
    export variables, but when the ``-e`` option is present an environment must
    exist or you will get an error.

    If no arguments are specified, this ``--help`` text is output.
    """  # noqa

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'arg',
            nargs='*',
            help='Command arguments',
            default=['psec', 'run', '--help'])
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        cmd = " ".join(
            [
                shlex.quote(a.encode('unicode-escape').decode())
                for a in parsed_args.arg
            ]
        )
        if self.app_args.export_env_vars:
            se.requires_environment()
            se.read_secrets_and_descriptions()
        return call(cmd, shell=True)  # nosec


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
