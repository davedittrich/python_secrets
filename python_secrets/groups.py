# -*- coding: utf-8 -*-

import collections
import logging
import os
import posixpath
import yamlreader

from cliff.lister import Lister
from python_secrets.utils import *


def items_in_file(yamlfile):
    d = yamlreader.yaml_load(yamlfile)
    return len(d)

class Groups(Lister):
    """Show a list of secrets groups.

    The names of the groups and number of items are printed by default.
    """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('listing secret groups')
        groups_dir = self.app.get_secrets_descriptions_dir()

        # Ignore .order file and any other non-YAML file extensions
        extensions = ['yml', 'yaml']
        file_names = [fn for fn in os.listdir(groups_dir)
                      if any(fn.endswith(ext) for ext in extensions)]

        return (('Group', 'Items'),
                ((os.path.splitext(n)[0], items_in_file(posixpath.join(groups_dir, n))) for n in file_names)
                )
