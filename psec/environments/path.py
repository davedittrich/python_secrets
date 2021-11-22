# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.command import Command
from psec.secrets_environment import SecretsEnvironment


class EnvironmentsPath(Command):
    """Return path to files and directories for environment."""

    logger = logging.getLogger(__name__)

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

            Using the ``--exists`` option will just exit with return code ``0``
            when the environment directory exists, or ``1`` if it does not, and
            no path is printed on stdout.

            To append subdirectory components, provide them as arguments and
            they will be concatenated with the appropriate OS path separator.

            .. code-block:: console

                $ psec environments path -e goSecure configs
                /Users/dittrich/.secrets/goSecure/configs

            ..

            To ensure the directory path specified by command line arguments
            is present in the file system, use the ``--create`` option.

            Using the ``--tmpdir`` option will return the path to the temporary
            directory for the environment.  If the environment's directory
            already exists, the temporary directory will be also be created
            so it is ready for use.  If the environment directory does not
            already exist, the program will exit with an error message. Again,
            the ``--create`` changes this behavior and the missing directory
            path will be created.
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
        self.logger.debug('[*] returning environment path')
        environment = self.app.options.environment
        e = SecretsEnvironment(environment)
        if parsed_args.tmpdir:
            if not e.environment_exists() and not parsed_args.create:
                return (f"[-] environment '{str(e)}' does not exist; "
                        "use '--create' to create it")
            tmpdir = e.tmpdir_path(create_path=parsed_args.create)
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
                    self.logger.info("[+] created %s", full_path)
            if parsed_args.exists:
                # Just check existance and return result
                exists = os.path.exists(full_path)
                if self.app_args.verbose_level > 1:
                    status = "exists" if exists else "does not exist"
                    self.logger.info(
                        "[+] environment path '%s' %s",
                        full_path,
                        status
                    )
                return 0 if exists else 1
            else:
                self._print(full_path, parsed_args.json)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
