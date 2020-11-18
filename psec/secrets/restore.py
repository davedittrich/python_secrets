# -*- coding: utf-8 -*-

import argparse
import logging
import os
import tarfile
import textwrap

from cliff.command import Command
# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass
from sys import stdin


class SecretsRestore(Command):
    """Restore secrets and descriptions from a backup file."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('backup', nargs='?', default=None)
        parser.epilog = textwrap.dedent("""
            TODO(dittrich): Finish documenting command.
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] restore secrets')
        secrets = self.app.secrets
        secrets.requires_environment()
        backups_dir = os.path.join(
            secrets.environment_path(),
            "backups")
        backups = [fn for fn in
                   os.listdir(backups_dir)
                   if fn.endswith('.tgz')]
        if parsed_args.backup is not None:
            choice = parsed_args.backup
        elif not (stdin.isatty() and 'Bullet' in globals()):
            # Can't involve user in getting a choice.
            raise RuntimeError('[-] no backup specified for restore')
        else:
            # Give user a chance to choose.
            choices = ['<CANCEL>'] + sorted(backups)
            cli = Bullet(prompt="\nSelect a backup from which to restore:",
                         choices=choices,
                         indent=0,
                         align=2,
                         margin=1,
                         shift=0,
                         bullet="→",
                         pad_right=5)
            choice = cli.launch()
            if choice == "<CANCEL>":
                self.LOG.info('cancelled restoring from backup')
                return
        backup_path = os.path.join(backups_dir, choice)
        with tarfile.open(backup_path, "r:gz") as tf:
            # Only select intended files. See warning re: Tarfile.extractall()
            # in https://docs.python.org/3/library/tarfile.html
            allowed_prefixes = ['secrets.json', 'secrets.d/']
            names = [fn for fn in tf.getnames()
                     if any(fn.startswith(prefix)
                            for prefix in allowed_prefixes
                            if '../' not in fn)
                     ]
            env_path = secrets.environment_path()
            for name in names:
                tf.extract(name, path=env_path)
        self.LOG.info(f'[+] restored backup {backup_path} to {env_path}')


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
