# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.utils
import textwrap

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import colors
    from bullet import Input
    from bullet import YesNo
except ModuleNotFoundError:
    pass

from cliff.command import Command
from prettytable import PrettyTable
from psec.secrets import SECRET_TYPES
from psec.utils import find
from sys import stdin


def get_description(name=None, defaults=None):
    """Prompt user for description fields and return results."""
    new_description = dict()
    # Variable name is required (obviously)
    new_description['Variable'] = defaults['Variable']
    # Variable type is required (obviously)
    original_type = defaults.get('Type', None)
    type_hint = "" if original_type is None else f" [was '{original_type}']"
    new_description['Type'] = psec.utils.prompt_options_list(
        prompt=f"Variable type{type_hint}: ",
        default=original_type,
        options=[item['Type'] for item in SECRET_TYPES]
    )
    # Prompt (also serves as description) is required
    prompt = ("Descriptive string to prompt user when "
              "setting value: ")
    cli = Input(prompt,
                default=defaults.get('Prompt'),
                word_color=colors.foreground["yellow"])
    result = cli.launch()
    new_description['Prompt'] = result
    # Alternative option set is (no pun intended) optional
    if new_description['Type'] in ['string']:
        prompt = "Acceptable options from which to chose: "
        cli = Input(prompt,
                    default=defaults.get('Options'),
                    word_color=colors.foreground["yellow"])
        result = cli.launch()
        # TODO(dittrich): BUG or ISSUE in waiting.
        # Items in an Options list can't end in '.*' without
        # causing confusion with ',*' wildcard feature.
        # Maybe switch to using '|' for alternaives instead?
        if '.*' in result:
            if result == '.*':
                msg = "[-] '.*' is not valid: did you mean '*'?"
            else:
                msg = ("[-] options list items can't have '.*' "
                       "wildcards: did you mean to end with ',*'?")
            raise RuntimeError(msg)
        new_description['Options'] = result
    # Environment variable export alternative optional
    prompt = "Environment variable to export: "
    cli = Input(prompt,
                default=defaults.get('Export', ' '),
                word_color=colors.foreground["yellow"])
    result = cli.launch()
    if result not in [' ', '', None]:
        new_description['Export'] = result
    print('')
    return new_description


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
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Create missing environment and/or group (default: False)"
        )
        parser.add_argument(
            '--update',
            action='store_true',
            dest='update',
            default=False,
            help=("Update the fields in an existing description "
                  "(default: False)")
        )
        parser.add_argument(
            '--mirror-locally',
            action='store_true',
            dest='mirror_locally',
            default=False,
            help="Mirror definitions locally (default: False)"
        )
        parser.add_argument('arg', nargs='*', default=None)
        parser.epilog = textwrap.dedent("""
            Defines one or more secrets in a specified group based on
            input from the user. Secret definitions are created in the
            user's environments storage directory and a new variable with
            no value is created there, too.

            If the environment and/or the group does not exist, you will be
            prompted to create them. Use the ``--force`` option to create them
            without asking.

            To maintain a copy of the secrets descriptions in the source
            repository so they can be used to quickly configure a new
            deployment after cloning, use the ``--mirror-locally`` option when
            creating secrets from the root of the repository directory. A
            copy of each modified group description file will be mirrored
            into a subdirectory tree in the current working directory where
            you can commit it to the repository.

            If no group is specified with the ``--group`` option, the
            environment identifier will be used as a default. This simplifies
            things for small projects that don't need the drop-in style group
            partitioning that is more appropriate for multi-tool open source
            system integration where a single monolithic configuration file
            becomes unwieldy and inflexible. This feature can also be used
            for "global" variables that could apply across sub-components.

            .. code-block:: console

                $ psec secrets create newsecret --force

            ..

            KNOWN LIMITATION: This subcommand currently only works interactively
            and you will be prompted for all attributes. In future, this may be
            handled using ``key=value`` pairs for attributes, similar to the way
            the ``secrets set`` command works.

            """)  # noqa
        # TODO(dittrich): address the known limitation
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] creating secrets')
        # Does an environment already exist?
        if not stdin.isatty():
            raise RuntimeError(
                '[-] this command only works when a TTY is available')
        se = self.app.secrets
        env = se.environment
        if not se.environment_exists():
            if parsed_args.update:
                raise RuntimeError(
                    f"[!] environment '{env}' does not exist'")
            client = YesNo(f"create environment '{env}'? ",
                           default='n')
            res = client.launch()
            if not res:
                self.LOG.info('[!] cancelled creating environment')
                return 1
            se.environment_create()
            self.LOG.info(
                f"[+] environment '{env}' "
                f"({se.environment_path()}) created")
        if parsed_args.update and len(parsed_args.arg) > 1:
            # TODO(dittrich): Refactor to loop over parsed_arg.arg
            # from here (not farther down).
            raise RuntimeError(
                "[!] only one variable can be updated at a time")
        se.read_secrets_and_descriptions()
        groups = se.get_groups()
        group = parsed_args.group
        if group is None:
            if not parsed_args.update:
                # Default group to same name as environment identifier
                group = env
            else:
                group = se.get_group(parsed_args.arg[0])
        if group not in groups:
            if parsed_args.update:
                raise RuntimeError(
                    f"[!] group '{group}' does not exist'")
            client = YesNo(f"create new group '{group}'? ",
                           default='n')
            res = client.launch()
            if not res:
                self.LOG.info('[!] cancelled creating group')
                return 1
            descriptions = list()
            variables = list()
        else:
            descriptions = se.read_descriptions(group=group)
            variables = [item['Variable'] for item in descriptions]
        args = parsed_args.arg
        changed = False
        for arg in args:
            arg_row = find(descriptions, 'Variable', arg)
            if parsed_args.update:
                if arg not in variables:
                    self.LOG.info(
                        f"[-] can't update nonexistent variable '{arg}'")
                    continue
                self.LOG.info(
                    f"[+] updating variable '{arg}' in group '{group}'")
                new_description = get_description(
                    name=arg,
                    defaults=descriptions[arg_row]
                )
            else:
                if arg in variables:
                    self.LOG.info(f"[-] variable '{arg}' already exists")
                    continue
                self.LOG.info(
                    f"[+] creating variable '{arg}' in group '{group}'")
                new_description = get_description(
                    name=arg,
                    defaults={
                        'Variable': arg,
                        'Prompt': f"Value for '{arg}'",
                        'Options': "*",
                        'Export': " ",
                    }
                )
            if len(new_description):
                table = PrettyTable()
                table.field_names = ('Key', 'Value')
                table.align = 'l'
                for k, v in new_description.items():
                    table.add_row((k, v))
                print(table)
                client = YesNo("commit this description? ",
                               default='n')
                res = client.launch()
                if not res:
                    continue
                if arg_row is not None:
                    descriptions[arg_row] = new_description
                else:
                    descriptions.append(new_description)
                    se.set_secret(arg)
                changed = True
        if changed:
            se.write_descriptions(
                data=descriptions,
                group=group,
                mirror_to=os.getcwd() if parsed_args.mirror_locally else None)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
