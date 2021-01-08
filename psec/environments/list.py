# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import psec.utils
import textwrap
import sys

from . import default_environment
from . import _is_default

from cliff.lister import Lister


class EnvironmentsList(Lister):
    """List the current environments."""

    LOG = logging.getLogger(__name__)

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
            """)

        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] listing environment(s)')
        secrets_environment = psec.secrets.SecretsEnvironment()
        default_env = default_environment()
        columns = (['Environment', 'Default'])
        basedir = secrets_environment.secrets_basedir()
        if parsed_args.aliasing:
            columns.append('AliasFor')
        data = list()
        environments = os.listdir(basedir)
        for e in sorted(environments):
            env_path = os.path.join(basedir, e)
            if psec.secrets.is_valid_environment(env_path,
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
        if not len(data):
            sys.exit(1)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
