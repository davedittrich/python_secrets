# -*- coding: utf-8 -*-

import collections
import logging
import posixpath
import yaml

from cliff.formatters.json_format import JSONFormatter
from cliff.formatters.table import TableFormatter
from cliff.lister import Lister
from python_secrets.utils import *


class Secrets(Lister):
    """List the contents of the secrets file"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Secrets, self).get_parser(prog_name)
        parser.add_argument(
            '-C', '--no-redact',
            action='store_false',
            dest='redact',
            default=True,
            help="Do not redact table output (all other formats are cleartext (default: False)"
        )
        return parser

    def take_action(self, parsed_args):
        dirname = posixpath.join(self.app_args.secrets_dir, self.app_args.environment)
        fname = posixpath.join(dirname, self.app_args.secrets_file)
        the_secrets = collections.OrderedDict()
        with open(fname, 'r') as f:
            the_secrets = yaml.load(f)
        columns = ('Variable', 'Value')
        is_table = type(self.formatter) is TableFormatter
        is_json = type(self.formatter) is JSONFormatter

        data = (
            [(k, redact(v, is_table and parsed_args.redact))
              for k, v in the_secrets.items()])
        return columns, data

# EOF
