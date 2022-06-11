# -*- coding: utf-8 -*-

import logging
import os
import sys

from cliff.lister import Lister
from psec.utils import (
    get_default_environment,
    get_environment_paths,
    is_valid_environment,
)


class EnvironmentsList(Lister):
    """
    List the current environments.

    You can get a list of all available environments at any time, including
    which one would be the default used by sub-commands::

        $ psec environments list
        +-------------+---------+
        | Environment | Default |
        +-------------+---------+
        | development | No      |
        | testing     | No      |
        | production  | No      |
        +-------------+---------+


    To see which environments are aliases, use the ``--aliasing`` option::

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


    If there are any older environments that contain ``.yml`` files for storing
    secrets or definitions, they will be called out when you list environments.
    (Adding ``-v`` will explicitly list the names of files that are found if
    you wish to see them.)::

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
    """  # noqa

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--aliasing',
            action='store_true',
            dest='aliasing',
            default=False,
            help='Include aliasing'
        )
        return parser

    def take_action(self, parsed_args):
        default_env = get_default_environment()
        self.logger.debug(
            "[+] using secrets basedir '%s'",
            self.app.secrets_basedir,
        )
        columns = (['Environment', 'Default'])
        if parsed_args.aliasing:
            columns.append('AliasFor')
        data = list()
        for env_path in get_environment_paths(basedir=self.app.secrets_basedir):  # noqa
            if is_valid_environment(
                env_path,
                self.app_args.verbose_level,
            ):
                is_default = (
                    "Yes" if env_path.name == default_env
                    else "No"
                )
                if not parsed_args.aliasing:
                    item = (env_path.name, is_default)
                else:
                    try:
                        alias_for = os.path.basename(os.readlink(env_path))
                    except OSError:
                        alias_for = ''
                    item = (env_path.name, is_default, alias_for)
                data.append(item)
        if len(data) == 0:
            sys.exit(1)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
