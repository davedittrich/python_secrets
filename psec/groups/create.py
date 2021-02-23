# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import textwrap

from cliff.command import Command


class GroupsCreate(Command):
    """Create a secrets descriptions group."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Group descriptions file to clone from (default: None)"
        )
        parser.add_argument('arg',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Secrets and variables are described in files in a drop-in
            style directory ending in ``.d``. This forms 'groups' that
            organize secrets and variables by purpose, by open source
            tool, etc. This command creates a new group descriptions
            file in the selected environment.

            When integrating a new open source tool or project with an
            existing tool or project, you can create a new group in the
            current environment and clone its secrets descriptions from
            pre-existing definitions. This does not copy any values, just
            the descriptions, allowing you to manage the values independently
            of other projects using a different environment.

            .. code-block:: console

                $ psec groups create newgroup --clone-from ~/git/goSecure/secrets.d/gosecure.json
                [+] created new group 'newgroup'
                $ psec groups list
                +----------+-------+
                | Group    | Items |
                +----------+-------+
                | jenkins  |     1 |
                | myapp    |     4 |
                | newgroup |    12 |
                | trident  |     2 |
                +----------+-------+

            ..

            Note: Directory and file permissions on cloned groups will prevent
            ``other`` from having read/write/execute permissions (i.e., ``o-rwx``
            in terms of the ``chmod`` command.)
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] creating group')
        se = self.app.secrets
        # Creating a new group in an empty environment that exists is OK.
        se.requires_environment(path_only=True)
        se.read_secrets_descriptions()
        # A cloned group can inherit its name from file, otherwise a
        # name is required.
        if parsed_args.arg is None and parsed_args.clone_from is None:
            raise RuntimeError(
                '[-] no group name or group description source specified')
        group = parsed_args.arg
        groups = se.get_groups()
        clone_from = parsed_args.clone_from
        # Default is to create a new empty group
        descriptions = dict()
        if clone_from is not None:
            # Are we cloning from a file?
            if clone_from.endswith('.json'):
                if not os.path.isfile(clone_from):
                    raise RuntimeError(
                        "[-] group description file "
                        f"'{clone_from}' does not exist")
                if group is None:
                    group = os.path.splitext(
                        os.path.basename(clone_from))[0]
                descriptions = se.read_descriptions(infile=clone_from)
            else:
                # Must be cloning from an environment, but which group?
                if group is None:
                    raise RuntimeError(
                        "[-] please specify which group from environment "
                        f"'{parsed_args.clone_from}' you want to clone")
                clonefrom_se = psec.secrets.SecretsEnvironment(
                    environment=clone_from
                )
                if group not in clonefrom_se.get_groups():
                    raise RuntimeError(
                        f"[-] group '{group}' does not exist in "
                        f"environment '{clone_from}'")
                descriptions = clonefrom_se.read_descriptions(group=group)
        if len(descriptions):
            se.check_duplicates(descriptions)
        if group in groups:
            raise RuntimeError(f"[-] group '{group}' already exists")
        self.LOG.info(f"[+] creating new group '{group}'")
        se.write_descriptions(
            data=descriptions,
            group=group)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
