# -*- coding: utf-8 -*-

import argparse
import logging
import os
import psec.secrets
import psec.utils
import textwrap

from cliff.command import Command
from stat import S_IMODE


class EnvironmentsPath(Command):
    """Return path to files and directories for environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--create',
            action='store_true',
            dest='create',
            default=False,
            help=("Create the directory path if it does not yet exist "
                  "(default: False)")
        )
        parser.add_argument(
            '--exists',
            action='store_true',
            dest='exists',
            default=False,
            help="Check to see if environment exists and" +
                 "return exit code (0==exists, 1==not)"
        )
        parser.add_argument(
            '--json',
            action='store_true',
            dest='json',
            default=False,
            help="Output in JSON (e.g., for Terraform external data source; " +
                 "default: False)"
        )
        parser.add_argument(
            '--tmpdir',
            action='store_true',
            dest='tmpdir',
            default=False,
            help='Create and/or return tmpdir for this environment ' +
                 '(default: False)'
        )
        parser.add_argument('subdir',
                            nargs='*',
                            default=None)
        parser.epilog = textwrap.dedent("""
            Provides the full absolute path to the environment directory
            for the environment and any specified subdirectories.

            .. code-block:: console

                $ psec environments path
                /Users/dittrich/.secrets/psec
                $ psec environments path -e goSecure
                /Users/dittrich/.secrets/goSecure

            ..

            Using the ``--exists`` option will just return ``0`` if the path
            exists, or ``1`` if it does not. No path is printed on stdout.

            Using the ``--tmpdir`` option will return the path to the
            temporary directory for the environment. If it does not already
            exist, it will be created so it is ready for use.

            To append subdirectory components, provide them as arguments and
            they will be concatenated with the appropriate OS path separator.

            .. code-block:: console

                $ psec environments path -e goSecure configs
                /Users/dittrich/.secrets/goSecure/configs

            ..

            To ensure the directory path specified by command line arguments
            is present, use the ``--create`` option.

            """)
        return parser

    def _print(self, item, use_json=False):
        """Output item, optionally using JSON"""
        if use_json:
            import json
            res = {'path': item}
            print(json.dumps(res))
        else:
            print(item)

    def take_action(self, parsed_args):
        self.LOG.debug('[*] returning environment path')
        environment = self.app.options.environment
        e = psec.secrets.SecretsEnvironment(environment)
        if parsed_args.tmpdir:
            tmpdir = e.tmpdir_path()
            tmpdir_mode = 0o700
            try:
                os.makedirs(tmpdir, tmpdir_mode)
                self.LOG.info(f"[+] created tmpdir {tmpdir}")
            except FileExistsError:
                mode = os.stat(tmpdir).st_mode
                current_mode = S_IMODE(mode)
                if current_mode != tmpdir_mode:
                    os.chmod(tmpdir, tmpdir_mode)
                    self.LOG.info(
                        f"[+] changed mode on {tmpdir} "
                        f"from {oct(current_mode)} to {oct(tmpdir_mode)}")
            finally:
                self._print(tmpdir, parsed_args.json)
        else:
            base_path = e.environment_path()
            subdir = parsed_args.subdir
            full_path = base_path if subdir is None \
                else os.path.join(base_path, *subdir)
            if not os.path.exists(full_path) and parsed_args.create:
                mode = 0o700
                os.makedirs(full_path, mode)
                if self.app_args.verbose_level > 1:
                    self.LOG.info(f"[+] created {full_path}")
            if parsed_args.exists:
                # Just check existance and return result
                exists = os.path.exists(full_path)
                if self.app_args.verbose_level > 1:
                    status = "exists" if exists else "does not exist"
                    self.LOG.info(
                        f"[+] environment path '{full_path}' {status}")
                return 0 if exists else 1
            else:
                self._print(full_path, parsed_args.json)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
