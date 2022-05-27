# -*- coding: utf-8 -*-

import json
import logging
import sys
import yaml

from pathlib import Path
from typing import Union
from cliff.command import Command
from psec.utils import safe_delete_file


logger = logging.getLogger(__name__)


def get_yaml_files_from_path(path: Path) -> list:
    """
    Return all YAML files from directory.
    """
    return [
        fname for fname in path.iterdir()
        if fname.suffix.lower() in ['.yml', '.yaml']
    ]


def update_from_yaml(
    path: Path = Path('secrets/secrets.d'),
    keep_original=False,
    verbose=False
):
    """
    Helper function to convert old YAML style directories.
    """
    yaml_files = get_yaml_files_from_path(path)
    for yaml_file in yaml_files:
        # json_file = f"{os.path.splitext(yaml_file)[0]}.json"
        json_file = yaml_file.with_suffix('.json')
        if verbose:
            logger.info("[+] converting '%s' to JSON", yaml_file)
        yaml_to_json(yaml_file=yaml_file, json_file=json_file)
        if not keep_original:
            if verbose:
                logger.info("[+] removing '%s'", yaml_file)
            safe_delete_file(yaml_file)


def yaml_to_json(
    yaml_file: Union[Path, str, None] = None,
    json_file: Union[Path, str, None] = None,
):
    """
    Translate a YAML file (or stdin) to a JSON file (or stdout).
    """
    if yaml_file in ['-', None]:
        content = yaml.safe_load(sys.stdin.read())
        if not content:
            raise RuntimeError(
                '[-] failed to read YAML content from stdin'
            )
    else:
        if not isinstance(yaml_file, Path):
            raise TypeError(
                f"[-] 'yaml_file' must be '-' or Path: {str(yaml_file)}"
            )
        content = yaml.safe_load(yaml_file.read_text())
        if not content:
            raise RuntimeError(
                '[-] failed to read YAML content from '
                f"'{str(yaml_file)}'"
            )
    if json_file in ['-', None]:
        json.dump(content, sys.stdout, indent=2)
        sys.stdout.write('\n')
        sys.stdout.flush()
    else:
        json_file.write_text(json.dumps(content, indent=2))


class YAMLToJSON(Command):
    """
    Convert YAML file(s) to JSON file(s).

    You can specify one or more files or directories to convert (including '-'
    for standard input).

    By default the JSON format data will be written to standard output.  This
    is useful for one-off conversion of YAML content to see the resulting JSON,
    or to produce a file with a different name by redirecting into a new file.

    The ``--convert`` option writes the JSON to a file with the same base name,
    but with a ``.json`` extension, then deletes the original YAML file unless
    the ``--keep-original`` option is specified.  When a directory is passed as
    an argument with the ``--convert`` option, *all* files ending in ``.yml``
    in the directory will be processed.

    .. note::

        The original format for secrets files and secrets description files was
        YAML. The format was changed to JSON in a recent release, necessitating
        that existing secrets descriptions in repositories and/or existing
        secrets environments be converted.  As of now, this utility subcommand
        provides a mechanism for you to use in making this change. Future
        releases may include a more user-friendly upgrade mechanism.

        Here is a demonstration using an old YAML-style secrets descriptions
        directory used by tests in the ``tests/`` subdirectory::

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
    """

    logger = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=cmd_name)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--convert',
            action='store_true',
            dest='convert',
            default=False,
            help='Convert file(s) in place'
        )
        parser.add_argument(
            '--keep-original',
            action='store_true',
            dest='keep_original',
            default=False,
            help='Keep original YAML file after conversion'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=['-'],
            help='Files and/or directories convert'
        )
        return parser

    def take_action(self, parsed_args):
        if '-' in parsed_args.arg and parsed_args.convert:
            raise RuntimeError('[-] stdin cannot be used with ``--convert``')
        for arg in parsed_args.arg:
            json_file = '-'
            if arg == '-':
                yaml_to_json(
                    yaml_file=arg,
                    json_file=json_file,
                )
            else:
                path = Path(arg).absolute()
                if not path.exists():
                    raise RuntimeError(
                        f"[-] path does not exist: '{str(path)}'"
                    )
                if path.is_file():
                    if parsed_args.convert:
                        json_file = path.with_suffix('.json')
                        self.logger.info("[+] converting '%s'", path)
                    yaml_to_json(
                        yaml_file=path,
                        json_file=json_file,
                    )
                    if (
                        parsed_args.convert
                        and not parsed_args.keep_original
                    ):
                        if self.app_args.verbose_level >= 1:
                            self.logger.info("[+] removing '%s'", str(path))
                        safe_delete_file(str(path))
                elif path.is_dir():
                    if not parsed_args.convert:
                        raise RuntimeError(
                            "[-] must use '--convert' with directory "
                            f"'{str(path)}'"
                        )
                    update_from_yaml(
                        path=path,
                        keep_original=parsed_args.keep_original,
                        verbose=(self.app_args.verbose_level >= 1)
                    )


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
