# -*- coding: utf-8 -*-

"""
Initialize a psec secrets base directory.
"""

import logging

from cliff.command import Command

from psec.utils import (
    get_default_secrets_basedir,
    secrets_basedir_create,
)


class Init(Command):
    """
    Initialize a psec secrets base directory.

    The `psec` program stores secrets and variables for environments in their
    own subdirectory trees beneath a top level directory root referred to as the
    "secrets base directory" (`secrets_basedir`). This directory tree should not
    be a "normal" file system directory that includes arbitrary files and
    directories, but rather a special location dedicated to *only* storing
    secrets environments and related files.

    For added security, you can root this directory tree within an encrypted
    USB-connected disk device, SD card, or other external or remote file system
    that is only mounted when needed. This ensures sensitive data that are not
    being actively used are left encrypted in storage.  The `D2_SECRETS_BASEDIR`
    environment variable or `-d` option allow you to specify the directory to use.

    To attempt to prevent accidentally storing secrets in directories that
    are already storing normal files or directories, a special marker file must
    be present.  The `init` command ensures that this secrets base directory is
    created and marked by the presence of that special file. Until this is done,
    some `psec` commands may report the base directory is not found (if it
    does not exist) or is not valid (if it does exist, but does not contain
    the special marker file)::

        $ psec -d /tmp/foo/does/not/exist environments list
        [-] directory '/tmp/foo/does/not/exist' does not exist
    """  # noqa

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        try:
            basedir = self.app.secrets_basedir
        except AttributeError:
            # For cliff
            basedir = get_default_secrets_basedir()
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'basedir',
            nargs='?',
            default=basedir
        )
        return parser

    def take_action(self, parsed_args):
        secrets_basedir = parsed_args.basedir
        secrets_basedir_create(basedir=secrets_basedir)
        if self.app_args.verbose_level > 0:
            self.logger.info(
                "[+] directory '%s' is enabled for secrets storage",
                secrets_basedir
            )


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
