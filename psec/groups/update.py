# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import textwrap

from cliff.command import Command
from collections import OrderedDict
from operator import itemgetter


def compare_descriptions_lists(orig_list=list(), new_list=list()):
    """Compare two lists of secrets descriptions."""
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
        print(f"Variable '{v}' was added'")
    for v in removed_vars:
        print(f"Variable '{v}' was removed'")
    for v in common_vars:
        diff = DictDiffer(orig_list_as_dict.get(v),
                          new_list_as_dict.get(v))
        if not diff.different():
            print(f"Variable '{v}' is described the same")
        else:
            print(f"Variable '{v}' is described differently:")
            changed = diff.changed()


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values

    https://code.activestate.com/recipes/576644-diff-two-dictionaries/#c7
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def different(self):
        return len(self.added()) or len(self.removed()) or len(self.changed())

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


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
                group_files = [
                    f for f in os.listdir(parsed_args.update_from)
                    if f.endswith('.json')
                ]
                groups = [
                    os.path.splitext(os.path.basename(f))[0]
                    for f in group_files
                ]
                for group in groups:
                    orig_descriptions = se.get_group_definitions(group)
                    new_descriptions = from_se.read_descriptions(group=group)
                    new_descriptions[1] = OrderedDict({
                        'Variable': 'google_plex',
                        'Type': 'string',
                        'Prompt': 'How big is it'})
                    compare_descriptions_lists(orig_list=orig_descriptions,
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
