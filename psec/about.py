# -*- encoding: utf-8 -*-

"""
About the ``psec`` (``python_secrets``) CLI.
"""

import logging
import os

from collections import OrderedDict
from pathlib import Path

from cliff.show import ShowOne

from psec import __version__
from psec.utils import is_secrets_basedir


UNDEF = ''


class About(ShowOne):
    """
    About the ``psec`` (``python_secrets``) CLI.

    Prints out selected environment and internal state information
    useful for  better situational awareness of how ``psec`` will
    behave when testing, etc.::

        $ psec about
        +-----------------------------+-------------------------------------------------------------------------------+
        | Field                       | Value                                                                         |
        +-----------------------------+-------------------------------------------------------------------------------+
        | env:BROWSER                 | safari                                                                        |
        | env:CLIFF_FIT_WIDTH         | 1                                                                             |
        | env:CONDA_DEFAULT_ENV       | psec                                                                          |
        | env:D2_ENVIRONMENT          | python_secrets                                                                |
        | env:D2_LOGFILE              |                                                                               |
        | env:D2_SECRETS_BASEDIR      | /tmp/.psecsecrets                                                             |
        | env:D2_SECRETS_BASENAME     |                                                                               |
        | env:D2_NO_REDACT            |                                                                               |
        | environment                 | python_secrets                                                                |
        | executable_path             | /usr/local/Caskroom/miniconda/base/envs/psec/lib/python3.8/site-packages/psec |
        | secrets_basedir             | /tmp/.psecsecrets                                                             |
        | secrets_basedir_initialized | True                                                                          |
        | version                     | 21.2.1.dev8+gcbfdd3a.d20210623                                                |
        +-----------------------------+-------------------------------------------------------------------------------+
    """  # noqa

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        columns = []
        data = []
        info = OrderedDict({
            "env:BROWSER": os.getenv('BROWSER', UNDEF),
            "env:CLIFF_FIT_WIDTH": os.getenv('CLIFF_FIT_WIDTH', UNDEF),
            "env:CONDA_DEFAULT_ENV": os.getenv('CONDA_DEFAULT_ENV', UNDEF),
            "env:D2_ENVIRONMENT": os.getenv('D2_ENVIRONMENT', UNDEF),
            "env:D2_LOGFILE": os.getenv('D2_LOGFILE', UNDEF),
            "env:D2_SECRETS_BASEDIR": os.getenv('D2_SECRETS_BASEDIR', UNDEF),
            "env:D2_SECRETS_BASENAME": os.getenv('D2_SECRETS_BASENAME', UNDEF),
            "env:D2_NO_REDACT": os.getenv('D2_NO_REDACT', UNDEF),
            "environment": self.app.environment,
            "executable_path": Path(__file__).parent.absolute(),
            "secrets_basedir": self.app.secrets_basedir,
            "secrets_basedir_initialized": is_secrets_basedir(self.app.secrets_basedir),  # noqa
            "version": __version__
        })
        for key, value in info.items():
            columns.append(key)
            data.append(value)
        return columns, data


# EOF
