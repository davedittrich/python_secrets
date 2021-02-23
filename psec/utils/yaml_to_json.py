# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import textwrap
import sys
import yaml

from cliff.command import Command
from psec.utils import safe_delete_file
from psec.utils import get_files_from_path

logger = logging.getLogger(__name__)


def update_from_yaml(
    path='secrets/secrets.d',
    keep_original=False,
    verbose=False
):
    """Helper function to convert old YAML style directories."""
    yaml_files = [
        fn for fn in get_files_from_path(path)
        if fn.endswith('.yml')
    ]
    for yaml_file in yaml_files:
        # json_file = f"{os.path.splitext(yaml_file)[0]}.json"
        json_file = yaml_file.replace('.yml', '.json')
        if verbose:
            logger.info(f"[+] converting '{yaml_file}' to JSON")
        yaml_to_json(yaml_file=yaml_file, json_file=json_file)
        if not keep_original:
            if verbose:
                logger.info(f"[+] removing '{yaml_file}'")
            safe_delete_file(yaml_file)


def yaml_to_json(
    yaml_file=None,
    json_file=None
):
    """Translate a YAML file (or stdin) to a JSON file (or stdout)."""
    if yaml_file in ['-', None]:
        yml = yaml.safe_load(sys.stdin.read())
    else:
        with open(yaml_file, 'r') as yf:
            yml = yaml.safe_load(yf)
    if json_file in ['-', None]:
        json.dump(yml, sys.stdout, indent=2)
        sys.stdout.write('\n')
        sys.stdout.flush()
    else:
        with open(json_file, 'w') as jf:
            json.dump(yml, jf, indent=2)
            jf.write('\n')
            jf.flush()


class YAMLToJSON(Command):
    """Convert YAML file(s) to JSON file(s)."""

    log = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=cmd_name)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--convert',
            action='store_true',
            dest='convert',
            default=False,
            help="Convert YAML to JSON format (default: False)"
        )
        parser.add_argument(
            '--keep-original',
            action='store_true',
            dest='keep_original',
            default=False,
            help="Keep original YAML file after conversion (default: False)"
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=['-'],
            help=("Files and/or directories convert "
                  "(default: standard input)")
        )
        parser.epilog = textwrap.dedent("""
            Utility to convert YAML format file(s) to JSON format.

            You can specify one or more files or directories to convert
            (including '-' for standard input). By default the JSON format
            data will be written to standard output.  This is useful for
            one-off conversion of YAML content to see the resulting JSON, or
            to produce a file with a different name by redirecting into a
            new file.

            The ``--convert`` option writes the JSON to a file with the same
            base name, but with the ``.json`` extension, then deletes the
            original YAML file. If you need to keep the original YAML file,
            add the ``--keep-original`` option.  If a directory is passed as
            an argument with the ``--convert`` option, *all* files ending in
            ``.yml`` in the directory will be processed.

            .. note::

                The original format for secrets files and secrets
                description files was YAML. The format was changed to
                JSON in a recent release, necessitating that existing
                secrets descriptions in repositories and/or existing
                secrets environments be converted.  As of now, this
                utility subcommand provides a mechanism for you to use
                in making this change. Future releases may include a
                more user-friendly upgrade mechanism.

                Here is a demonstration using an old YAML-style secrets
                descriptions directory used by tests in the ``tests/``
                subdirectory::

                    $ cp -r tests/secrets /tmp
                    $ tree /tmp/secrets/
                    /tmp/secrets/
                    └── secrets.d
                        ├── jenkins.yml
                        ├── myapp.yml
                        ├── oauth.yml
                        └── trident.yml

                    1 directory, 4 files
                    $ psec utils yaml-to-json --convert /tmp/secrets/secrets.d
                    [+] converting '/tmp/secrets/secrets.d/jenkins.yml' to JSON
                    [+] removing '/tmp/secrets/secrets.d/jenkins.yml'
                    [+] converting '/tmp/secrets/secrets.d/myapp.yml' to JSON
                    [+] removing '/tmp/secrets/secrets.d/myapp.yml'
                    [+] converting '/tmp/secrets/secrets.d/trident.yml' to JSON
                    [+] removing '/tmp/secrets/secrets.d/trident.yml'
                    [+] converting '/tmp/secrets/secrets.d/oauth.yml' to JSON
                    [+] removing '/tmp/secrets/secrets.d/oauth.yml'
                    $ tree /tmp/secrets/
                    /tmp/secrets/
                    └── secrets.d
                        ├── jenkins.json
                        ├── myapp.json
                        ├── oauth.json
                        └── trident.json

                    1 directory, 4 files


        """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[*] converting from YAML to JSON file format')
        if '-' in parsed_args.arg and parsed_args.convert:
            raise RuntimeError('[-] stdin cannot be used with ``--convert``')
        for arg in parsed_args.arg:
            path = os.path.abspath(arg) if arg != '-' else arg
            if parsed_args.convert:
                update_from_yaml(path=path,
                                 keep_original=parsed_args.keep_original,
                                 verbose=(self.app_args.verbose_level >= 1))
            elif path == '-':
                yaml_to_json(yaml_file=path)
            else:
                yaml_files = [
                    fn for fn in get_files_from_path(path)
                    if fn.endswith('.yml')
                ]
                for yaml_file in yaml_files:
                    self.log.info(f"[+] converting '{yaml_file}")
                    yaml_to_json(yaml_file=yaml_file)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
