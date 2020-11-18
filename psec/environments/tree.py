# -*- coding: utf-8 -*-

import argparse
import logging
import psec.secrets
import psec.utils
import sys
import textwrap

from cliff.command import Command


class EnvironmentsTree(Command):
    """Output tree listing of files/directories in environment."""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--no-files',
            action='store_true',
            dest='no_files',
            default=False,
            help='Do not include files in listing ' +
                 '(default: False)'
        )
        parser.add_argument('environment',
                            nargs='?',
                            default=None)
        parser.epilog = textwrap.dedent("""
            The ``environments tree`` command produces output similar
            to the Unix ``tree`` command:

            .. code-block:: console

                $ psec -e d2 environments tree
                /Users/dittrich/.secrets/d2
                ├── backups
                │   ├── black.secretsmgmt.tk
                │   │   ├── letsencrypt_2018-04-06T23:36:58PDT.tgz
                │   │   └── letsencrypt_2018-04-25T16:32:20PDT.tgz
                │   ├── green.secretsmgmt.tk
                │   │   ├── letsencrypt_2018-04-06T23:45:49PDT.tgz
                │   │   └── letsencrypt_2018-04-25T16:32:20PDT.tgz
                │   ├── purple.secretsmgmt.tk
                │   │   ├── letsencrypt_2018-04-25T16:32:20PDT.tgz
                │   │   ├── trident_2018-01-31T23:38:48PST.tar.bz2
                │   │   └── trident_2018-02-04T20:05:33PST.tar.bz2
                │   └── red.secretsmgmt.tk
                │       ├── letsencrypt_2018-04-06T23:45:49PDT.tgz
                │       └── letsencrypt_2018-04-25T16:32:20PDT.tgz
                ├── dittrich.asc
                ├── keys
                │   └── opendkim
                │       └── secretsmgmt.tk
                │           ├── 201801.private
                │           ├── 201801.txt
                │           ├── 201802.private
                │           └── 201802.txt
                ├── secrets.d
                │   ├── ca.json
                │   ├── consul.json
                │   ├── jenkins.json
                │   ├── rabbitmq.json
                │   ├── trident.json
                │   ├── vncserver.json
                │   └── zookeper.json
                ├── secrets.json
                └── vault_password.txt

            ..

            To just see the directory structure and not files, add
            the ``--no-files`` option:

            .. code-block:: console

                $ psec -e d2 environments tree --no-files
                /Users/dittrich/.secrets/d2
                ├── backups
                │   ├── black.secretsmgmt.tk
                │   ├── green.secretsmgmt.tk
                │   ├── purple.secretsmgmt.tk
                │   └── red.secretsmgmt.tk
                ├── keys
                │   └── opendkim
                │       └── secretsmgmt.tk
                └── secrets.d

            ..

            """)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('[*] outputting environment tree')
        environment = parsed_args.environment
        if environment is None:
            environment = self.app.options.environment
        e = psec.secrets.SecretsEnvironment(
            environment=environment)
        e.requires_environment()
        print_files = bool(parsed_args.no_files is False)
        psec.utils.atree(e.environment_path(),
                         print_files=print_files,
                         outfile=sys.stdout)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
