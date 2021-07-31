# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap
import sys

from cliff.lister import Lister
from psec.secrets_environment import (
    get_default_environment,
    _is_default,
    is_valid_environment,
)


class EnvironmentsList(Lister):
    """List the current environments."""

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--aliasing',
            action='store_true',
            dest='aliasing',
            default=False,
            help="Include aliasing (default: False)"
        )
        parser.epilog = textwrap.dedent("""
            You can get a list of all available environments at any time,
            including which one would be the default used by sub-commands:

            .. code-block:: console

                $ psec environments list
                +-------------+---------+
                | Environment | Default |
                +-------------+---------+
                | development | No      |
                | testing     | No      |
                | production  | No      |
                +-------------+---------+

            ..

            To see which environments are aliases, use the ``--aliasing``
            option.

            .. code-block:: console

                $ psec -v environments create --alias evaluation testing
                $ psec environments list --aliasing
                +-------------+---------+----------+
                | Environment | Default | AliasFor |
                +-------------+---------+----------+
                | development | No      |          |
                | evaluation  | No      | testing  |
                | testing     | No      |          |
                | production  | No      |          |
                +-------------+---------+----------+

            ..

            If there are any older environments that contain ``.yml`` files for storing
            secrets or definitions, they will be called out when you list environments.
            (Adding ``-v`` will explicitly list the names of files that are found if
            you wish to see them.)

            .. code-block:: console

                $ psec environments list
                [!] environment 'algo' needs conversion (see 'psec utils yaml-to-json --help')
                [!] environment 'hypriot' needs conversion (see 'psec utils yaml-to-json --help')
                [!] environment 'kali-packer' needs conversion (see 'psec utils yaml-to-json --help')
                +-------------------------+---------+
                | Environment             | Default |
                +-------------------------+---------+
                | attack_range            | No      |
                | attack_range_local      | No      |
                | flash                   | No      |
                | python_secrets          | Yes     |
                +-------------------------+---------+

            """)  # noqa

        return parser

    def take_action(self, parsed_args):
        self.logger.debug('[*] listing environment(s)')
        default_env = get_default_environment()
        columns = (['Environment', 'Default'])
        basedir = self.app.secrets.secrets_basedir()
        if parsed_args.aliasing:
            columns.append('AliasFor')
        data = list()
        environments = os.listdir(basedir)
        for e in sorted(environments):
            env_path = os.path.join(basedir, e)
            if is_valid_environment(env_path,
                                    self.app_args.verbose_level):
                default = _is_default(e, default_env)
                if not parsed_args.aliasing:
                    item = (e, default)
                else:
                    try:
                        alias_for = os.path.basename(os.readlink(env_path))
                    except OSError:
                        alias_for = ''
                    item = (e, default, alias_for)
                data.append(item)
        if len(data) == 0:
            sys.exit(1)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
