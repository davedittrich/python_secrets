# -*- coding: utf-8 -*-

"""
Back up just secrets and descriptions.
"""

import contextlib
import datetime
import logging
import os
import tarfile

from cliff.command import Command


@contextlib.contextmanager
def cd(path):
    """Change directory."""
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


class SecretsBackup(Command):
    """
    Back up just secrets and descriptions.

    Creates a backup (``tar`` format) of the secrets.json file
    and all description files.
    """

    logger = logging.getLogger(__name__)

    # def get_parser(self, prog_name):
    #     parser = super().get_parser(prog_name)
    #     return parser

    def take_action(self, parsed_args):
        secrets = self.app.secrets
        secrets.requires_environment()
        backups_dir = os.path.join(
            secrets.get_environment_path(),
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
        env_path = secrets.get_environment_path() + os.path.sep
        with cd(env_path):
            with tarfile.open(backup_path, "w:gz") as tf:
                tf.add(
                    secrets.get_secrets_file_path().replace(env_path, "", 1))
                tf.add(
                    secrets.get_descriptions_path().replace(env_path, "", 1))

        self.logger.info("[+] created backup '%s'", backup_path)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
