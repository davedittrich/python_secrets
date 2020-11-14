# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.utils
import textwrap

from cliff.command import Command
from sys import stdin

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Input
    from bullet import colors
except ModuleNotFoundError:
    pass


class SecretsDelete(Command):
    """Delete secrets and their definitions."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-g', '--group',
            action='store',
            dest='group',
            default=None,
            help="Group from which to delete the secret(s) (default: None)"
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Mandatory confirmation (default: False)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            Deletes one or more secrets and their definitions from an
            environment. Unless the ``--force`` flag is specified, you will
            be prompted to type in the variable name again to ensure you
            really want to remove all trace of it from the environment.

            .. code-block:: console

                $ psec secrets delete --group myapp myapp_client_psk myapp_client_ssid
                Type the name 'myapp_client_psk' to confirm: myapp_client_psk
                Type the name 'myapp_client_ssid' to confirm: myapp_client_ssid

            ..

            KNOWN LIMITATION: You must specify the group with the ``--group``
            option currently and are restricted to deleting variables from
            one group at a time.
            """)  # noqa
        # TODO(dittrich): address the known limitation
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('deleting secrets')
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
        variables = [item['Variable'] for item in descriptions]
        args = parsed_args.arg
        for arg in args:
            if arg not in variables:
                raise RuntimeError(
                    f"variable '{arg}' does not exist in group '{group}'")
            if not parsed_args.force:
                if not stdin.isatty():
                    raise RuntimeError(
                        '[-] must use "--force" flag to delete a secret.')
                else:
                    prompt = f"Type the name '{arg}' to confirm: "
                    cli = Input(prompt,
                                default="",
                                word_color=colors.foreground["yellow"])
                    confirm = cli.launch()
                    if confirm != arg:
                        self.LOG.info('cancelled deleting secret')
                        return
            descriptions = [
                item for item in descriptions
                if item['Variable'] != arg
            ]
            self.app.secrets.delete_secret(arg)
        if not len(descriptions):
            self.LOG.info(f"deleting empty group '{group}'")
            psec.utils.safe_delete_file(group_source)
        else:
            self.app.secrets.write_descriptions(
                data=descriptions,
                outfile=group_source)
            self.app.secrets.write_secrets()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
