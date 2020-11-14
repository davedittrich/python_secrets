# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.utils
import textwrap

from cliff.command import Command
from psec.secrets import SECRET_TYPES


class SecretsCreate(Command):
    """Create a new secret definition."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--group',
            action='store',
            dest='group',
            default=None,
            help="Group in which to define the secret(s) (default: None)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            Defines one or more secrets in a specified group based on
            input from the user. This command is used to populate a
            template to be used when initially setting up a new project.

            .. code-block:: console

                $ psec secrets create [TODO(dittrich): finish...]

            ..

            KNOWN LIMITATION: This subcommand currently only works interactively
            and you will be prompted for all attributes. In future, this may be
            handled using ``key=value`` pairs for attributes, similar to the way
            the ``secrets set`` command works.

            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating secrets')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        group = parsed_args.group
        groups = self.app.secrets.get_groups()
        # Default to using a group with the same name as the environment,
        # for projects that require a group of "global" variables.
        if group is None:
            group = str(self.app.secrets)
        if group not in groups:
            raise RuntimeError(
                (
                    f"group '{group}' does not exist in "
                    f"environment '{str(self.app.secrets)}'"
                )
                if parsed_args.group is not None else
                "please specify a group with ``--group``"
            )
        group_source = os.path.join(
            self.app.secrets.descriptions_path(),
            f'{group}.json'
        )
        descriptions = self.app.secrets.read_descriptions(
            infile=group_source)
        starting_length = len(descriptions)
        variables = [item['Variable'] for item in descriptions]
        args = parsed_args.arg
        for arg in args:
            new_description = dict()
            if arg in variables:
                self.LOG.info(f"[-] variable '{arg}' already exists")
            else:
                self.LOG.info(
                    f"[+] creating variable '{arg}' in group '{group}'"
                    )
                # Variable name is required (obviously)
                new_description['Variable'] = arg
                # Variable type is required (obviously)
                new_description['Type'] = psec.utils.prompt_options_list(
                    prompt="Variable type",
                    options=[item['Type'] for item in SECRET_TYPES]
                )
                # Prompt (also serves as description) is required
                new_description['Prompt'] = psec.utils.prompt_string(
                    prompt=("Descriptive string to prompt user "
                            "when setting value"),
                    default=f"Value for '{arg}'"
                )
                # Alternative option set is (no pun intended) optional
                options = psec.utils.prompt_string(
                    prompt=("Acceptable options from which to chose "
                            "(RETURN for none)"),
                    default=None
                )
                if options is not None:
                    new_description['Options'] = options
                # Environment variable export alternative optional
                export = psec.utils.prompt_string(
                    prompt="Environment variable to export (RETURN for none)",
                    default=None
                )
                if export is not None:
                    new_description['Export'] = export
                print("")
                if len(new_description):
                    descriptions.append(new_description)
                    self.app.secrets.set_secret(arg)
        if len(descriptions) > starting_length:
            self.app.secrets.write_descriptions(
                data=descriptions,
                outfile=group_source)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
