# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import textwrap

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import YesNo
except ModuleNotFoundError:
    pass


from cliff.command import Command
# from collections import OrderedDict
from operator import itemgetter
from prettytable import PrettyTable


logger = logging.getLogger(__name__)


def compare_descriptions_lists(
    group=None,
    orig_list=None,
    new_list=None,
):
    """Compare two lists of secrets descriptions."""
    if orig_list is None:
        raise RuntimeError("new")
        # confirm_apply_group_changes(group=group,
        #                             orig_list)
    orig_list = sorted(orig_list, key=itemgetter('Variable'))
    orig_list_as_dict = {i.get('Variable'): i for i in orig_list}
    orig_vars = set(i.get('Variable') for i in orig_list)

    new_list = sorted(new_list, key=itemgetter('Variable'))
    new_list_as_dict = {i.get('Variable'): i for i in new_list}
    new_vars = set(i.get('Variable') for i in new_list)

    added_vars = new_vars - orig_vars
    removed_vars = orig_vars - new_vars
    common_vars = new_vars & orig_vars
    for v in added_vars:
        logger.info(f"[+] variable '{v}' was added'")
    for v in removed_vars:
        logger.info(f"[+] variable '{v}' was removed'")
    for v in common_vars:
        diff = DictDiffer(orig_dict=orig_list_as_dict.get(v),
                          new_dict=new_list_as_dict.get(v))
        if not diff.different():
            logger.debug(f"[+] variable '{v}' is described the same")
        else:
            logger.info(f"[+] description of '{v}' is different:")
            differences = [
                ('changed', list(diff.changed())),
                ('added', list(diff.added())),
                ('removed', list(diff.removed()))
            ]
            for difference, what in differences:
                if len(what):
                    confirm_apply_variable_changes(
                        variable=v,
                        difference=difference,
                        what=what,
                        orig_attributes=orig_list_as_dict.get(v),
                        new_attributes=new_list_as_dict.get(v)
                    )
                    client = YesNo("commit this description? ",
                                   default='n')
                    res = client.launch()
                    logger.info(f"[!] result is {res}")
            # if arg_row is not None:
            #     descriptions[arg_row] = new_description
            # else:
            #     descriptions.append(new_description)
            #     se.set_secret(arg)


def confirm_apply_group_changes(
    group=None,
    difference=None,
    what=None,
    orig_list=None,
    new_list=None
):
    """Confirm application of a group descriptions change."""
    if difference == 'added':
        for item in new_list:
            v = item.get('Variable')
            logger.info(f"[+] new variable '{v}'")
            table = PrettyTable()
            table.field_names = ('Attribute', 'Value')
            table.align = 'l'
            for k, v in item.items():
                table.add_row((k, v))
            print(table)
    elif difference == 'removed':
        for item in what:
            logger.info(
                f"[+] attribute '{what}' removed from "
                f"variable '{item}'")
    elif difference == 'changed':
        raise RuntimeError('WIP')
    else:
        raise RuntimeError('[!] should not get here')


def confirm_apply_variable_changes(
    variable=None,
    difference=None,
    what=None,
    orig_attributes=None,
    new_attributes=None
):
    """Confirm application of change in a variable's description."""
    if difference == 'added':
        logger.info(
            f"[+] new attribute{'' if len(what) == 1 else 's'} "
            f"'{','.join(what)}'")
        table = PrettyTable()
        table.field_names = ('Attribute', 'Value')
        table.align = 'l'
        for item in new_attributes:
            table.add_row((item, new_attributes.get(item)))
        print(table)
    elif difference == 'removed':
        for item in what:
            logger.info(
                f"[+] attribute '{item}' removed from "
                f"variable '{variable}'")
    elif difference == 'changed':
        raise RuntimeError('WIP')
    else:
        raise RuntimeError('[!] should not get here')


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values

    https://code.activestate.com/recipes/576644-diff-two-dictionaries/#c7
    """
    def __init__(
        self,
        orig_dict=None,
        new_dict=None
    ):
        self.new_dict, self.orig_dict = new_dict, orig_dict
        self.set_new = set(new_dict.keys())
        self.set_orig = set(orig_dict.keys())
        self.intersect = self.set_new.intersection(self.set_orig)

    def different(self):
        return (
            len(self.added()) or
            len(self.removed()) or
            len(self.changed())
        )

    def added(self):
        return self.set_new - self.intersect

    def removed(self):
        return self.set_orig - self.intersect

    def changed(self):
        return set(
            o for o
            in self.intersect
            if self.orig_dict[o] != self.new_dict[o]
        )

    def unchanged(self):
        return set(
            o for o
            in self.intersect
            if self.orig_dict[o] == self.new_dict[o]
        )


class GroupsUpdate(Command):
    """Update secrets descriptions."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--update-from',
            action='store',
            dest='update_from',
            default=None,
            help="Directory containing updates (default: None)"
        )
        parser.add_argument('arg',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Compares and updates secrets descriptions in one or more groups.
            This feature is intended for keeping up with changes that
            result after pulling a Git repo with new commits.

            Updates can include adding new secrets, removing secrets, or
            changing attributes in secret descriptions. The user will be
            presented with the updates and asked to confirm them.

            .. code-block:: console

                $ psec groups update --update-from secrets.d
                . . .

            ..
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] updating group(s)')
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_descriptions()
        update_from = parsed_args.update_from
        # Will default to all groups in the update_source directory
        # if none specified at this point.
        group = parsed_args.arg
        from_se = psec.secrets.SecretsEnvironment()
        new_descriptions = dict()
        if update_from is not None:
            # Are we updating from a file?
            if update_from.endswith('.json'):
                if not os.path.isfile(update_from):
                    raise RuntimeError(
                        "[-] group description file "
                        f"'{update_from}' does not exist")
                if group is None:
                    group = os.path.splitext(
                        os.path.basename(update_from))[0]
                new_descriptions = from_se.read_descriptions(
                    infile=update_from)
            elif update_from.endswith('.d'):
                descriptions_dir = os.path.abspath(update_from)
                group_files = [
                    os.path.join(descriptions_dir, f)
                    for f in os.listdir(parsed_args.update_from)
                    if f.endswith('.json')
                ]
                # groups = [
                #     os.path.splitext(os.path.basename(f))[0]
                #     for f in group_files
                # ]
                for f in group_files:
                    group = os.path.splitext(os.path.basename(f))[0]
                    orig_descriptions = se.get_group_definitions(group)
                    new_descriptions = from_se.read_descriptions(infile=f)
                    if orig_descriptions is None:
                        self.LOG.info(
                            f"[+] group '{group}' is new")
                        confirm_apply_group_changes(
                            group=group,
                            difference='added',
                            orig_list=orig_descriptions,
                            new_list=new_descriptions)
                    else:
                        compare_descriptions_lists(group=group,
                                                   orig_list=orig_descriptions,
                                                   new_list=new_descriptions)
            else:
                raise RuntimeError(
                    "[-] update source must be JSON file or .d directory: "
                    f"'{parsed_args.update_from}''")
        if len(new_descriptions):
            se.check_duplicates(new_descriptions)
        # se.write_descriptions(
        #     data=descriptions,
        #     group=group)
        # self.LOG.info(f"[+] created new group '{group}'")


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
