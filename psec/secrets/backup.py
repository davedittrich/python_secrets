# -*- coding: utf-8 -*-

import argparse
import contextlib
import datetime
import logging
import os
import tarfile
import textwrap

from cliff.command import Command


@contextlib.contextmanager
def cd(path):
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


class SecretsBackup(Command):
    """Back up just secrets and descriptions."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            Creates a backup (``tar`` format) of the secrets.json file
            and all description files.
            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] backup secrets')
        secrets = self.app.secrets
        secrets.requires_environment()
        backups_dir = os.path.join(
            secrets.environment_path(),
            "backups")
        if not os.path.exists(backups_dir):
            os.mkdir(backups_dir, mode=0o700)
        elif not os.path.isdir(backups_dir):
            raise RuntimeError(f"[-] {backups_dir} is not a directory")

        # '2020-03-01T06:11:16.572992+00:00'
        iso8601_string = datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc).isoformat().replace(":", "")
        backup_name = f"{secrets.environment}_{iso8601_string}.tgz"
        backup_path = os.path.join(backups_dir, backup_name)

        # Change directory to allow relative paths in tar file,
        # then force relative paths (there has to be a better way...
        # just not right now.)
        env_path = secrets.environment_path() + os.path.sep
        with cd(env_path):
            with tarfile.open(backup_path, "w:gz") as tf:
                tf.add(
                    secrets.secrets_file_path().replace(env_path, "", 1))
                tf.add(
                    secrets.descriptions_path().replace(env_path, "", 1))

        self.LOG.info(f"[+] created backup '{backup_path}'")


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
