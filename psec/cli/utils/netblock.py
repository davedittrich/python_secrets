# -*- coding: utf-8 -*-

import logging

from cliff.command import Command
from psec.utils import (
    get_myip,
    get_netblock,
)


class Netblock(Command):
    """
    Get network CIDR block(s) for IP from WHOIS lookup.

    Look up the network address blocks serving the specified IP address(es)
    using the Python ``IPWhois`` module.

    https://pypi.org/project/ipwhois/

    If no arguments are given, the routable address of the host on which
    ``psec`` is being run will be determined and used as the default.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=cmd_name)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'ip',
            nargs='*',
            default=[],
            help='IP address to use'
        )
        return parser

    def take_action(self, parsed_args):
        if len(parsed_args.ip) == 0:
            # TODO(dittrich): Just use random for now
            # until refactoring out the choice method.
            parsed_args.ip.append(get_myip(method='random'))
        for ip in parsed_args.ip:
            print(get_netblock(ip=ip))


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
