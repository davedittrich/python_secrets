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

logger = logging.getLogger(__name__)


def get_files_from_path(path=None):
    """Return a list of files associated with a path."""
    abspath = os.path.abspath(path)
    if os.path.isfile(abspath):
        files = [abspath]
    elif os.path.isdir(abspath):
        files = [
            os.path.join(abspath, fname)
            for fname in os.listdir(abspath)
        ]
    else:
        raise RuntimeError(f"[-] '{path}' must be a file or directory")
    return files


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
            logger.info(f"[+] Converting '{yaml_file}' to '{json_file}'")
        yaml_to_json(yaml_file=yaml_file, json_file=json_file)
        if not keep_original:
            if verbose:
                logger.info(f"[+] Removing '{yaml_file}'")
            safe_delete_file(yaml_file)


def yaml_to_json(
    yaml_file=None,
    json_file=None
):
    """Convert a YAML file (or stdin) to a JSON file (or stdout)."""
    if json_file in ['-', None]:
        json_file = sys.stdout
    if yaml_file in ['-', None]:
        yaml_file = sys.stdin
        # TODO(dittrich): Delete after testing
        # yml = yaml.safe_load(sys.stdinr)
        # json.dump(yml, json_file, indent=2)
    with open(yaml_file, 'r') as yf:
        yml = yaml.safe_load(yf)
    with open(json_file, 'w') as jf:
        json.dump(yml, jf, indent=2)

    # TODO(dittrich): Delete after testing
    # else:
    #     with open(yaml_file, 'r') as yf:
    #         yml = yaml.load(yf, Loader=c_safe_loader)
    #         with open(json_file, 'w') as jf:
    #             json.dump(yml, jf, indent=2)


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
            'path',
            nargs='*',
            default=['-'],
            help=("Path to files and/or directories convert "
                  "(default: standard input)")
        )
        parser.epilog = textwrap.dedent("""
            Utility to convert YAML format secrets and/or descriptions file(s)
            to JSON format. You can specify one or more files or directories
            to convert. If you specify a directory path, *all* files ending
            in ``.yml`` in the directory will be processed.

            The default when converting a file with the ``--convert`` option
            is to delete the YAML file after conversion. To keep the original,
            use the ``--keep-original`` option.
        """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('converting from YAML to JSON file format')
        if '-' in parsed_args.path:
            if len(parsed_args.path) > 1:
                raise RuntimeError('[-] stdin must be the only argument')
            yaml_to_json(yaml_file='-')
            sys.exit(0)
        for path in parsed_args.path:
            update_from_yaml(path=os.path.abspath(path),
                             keep_original=parsed_args.keep_original,
                             verbose=(self.app_args.verbose_level >= 1))
        # yaml_files = []
        # for path in parsed_args.path:
        #     yaml_files.extend([
        #         fn for fn in get_files_from_path(path)
        #         if fn.endswith('yml')
        #     ])
        # for yaml_file in yaml_files:
        #     json_file = f"{os.path.splitext(yaml_file)[0]}.json"
        #     if parsed_args.convert and self.app_args.verbose_level >= 1:
        #         logger.info(f"[+] Converting '{yaml_file}' to '{json_file}'")
        #     yaml_to_json(yaml_file=yaml_file,
        #                  json_file=json_file,
        #                  keep_original=parsed_args.keep_original
        #                  )


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
