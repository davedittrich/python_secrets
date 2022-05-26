# -*- coding: utf-8 -*-

# Standard imports
import textwrap

# External imports
import ipaddress
import logging

from cliff.command import Command
from cliff.lister import Lister
from psec.utils import (
    get_myip,
    get_myip_methods,
    get_netblock,
    myip_methods,
)


logger = logging.getLogger(__name__)
# NOTE(dittrich): To be DRY, we want to define this warning once, but
# to ensure cliff formatting is not messed up, we need to append this
# text to the epilog with the string '+' operator.
QUOTA_WARNING = textwrap.dedent("""
    WARNING: Any of the sites used by this command may limit the number
    of queries allowed from a given source in a given period of time and
    may temporarily block or reject attempts to use their service beyond
    the quota limit.
""")


class MyIP(Command):
    r"""
    Get currently active internet routable IPv4 address.

    Return the routable IP address of the host running this script using one of
    several publicly available free methods typically using HTTPS or DNS.

    The ``--cidr`` option expresses the IP address as a CIDR block to use in
    setting up firewall rules for this specific IP address.

    The ``--netblock`` option follows this lookup with another lookup using
    WHOIS to get the network provider's address range(s), in CIDR notation, to
    help with creating firewall rules that can work around dynamic addressing.
    This is not the most secure way to grant network access as it allows any
    customer using the same provider to also communicate through the firewall,
    but you have to admit that it is better than ``allow ANY``!  ¯\_(ツ)_/¯

    To see a table of the methods, use ``utils myip methods``.

    KNOWN LIMITATION: Some of the methods may not fully support IPv6 at this
    point. If you find one that doesn't work, try a different one.

    See also:
        https://linuxize.com/post/how-to-find-ip-address-linux/
        https://dev.to/adityathebe/a-handy-way-to-know-your-public-ip-address-with-dns-servers-4nmn
    """  # noqa

    # TODO(dittrich): Add environment variable defining preferred method

    logger = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=cmd_name)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        default_method = 'random'
        choices = get_myip_methods(include_random=True)
        parser.add_argument(
            '-M', '--method',
            action='store',
            dest='method',
            choices=choices,
            # type=lambda m: None if m == 'random' else m,
            default=default_method,
            help='Method to use for determining IP address'
        )
        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '-C', '--cidr',
            action='store_true',
            dest='cidr',
            default=False,
            help='Express the IP address as a CIDR block'
        )
        what.add_argument(
            '-N', '--netblock',
            action='store_true',
            dest='netblock',
            default=False,
            help='Return network CIDR block(s) for IP from WHOIS'
        )
        parser.epilog = QUOTA_WARNING
        return parser

    def take_action(self, parsed_args):
        interface = ipaddress.ip_interface(
            get_myip(method=parsed_args.method))
        if parsed_args.cidr:
            print(str(interface.with_prefixlen))
        elif parsed_args.netblock:
            print(get_netblock(ip=interface.ip))
        else:
            print(str(interface.ip))


class MyIPMethods(Lister):
    """
    Show methods for obtaining routable IP address.

    Provides the details of the methods coded into this app for
    obtaining this host's routable IP address::

        $ psec utils myip methods
        +-----------+-------+--------------------------------------------------------+
        | Method    | Type  | Source                                                 |
        +-----------+-------+--------------------------------------------------------+
        | akamai    | dns   | dig +short @ns1-1.akamaitech.net ANY whoami.akamai.net |
        | amazon    | https | https://checkip.amazonaws.com                          |
        | google    | dns   | dig +short @ns1.google.com TXT o-o.myaddr.l.google.com |
        | icanhazip | https | https://icanhazip.com/                                 |
        | infoip    | https | https://api.infoip.io/ip                               |
        | opendns_h | https | https://diagnostic.opendns.com/myip                    |
        | opendns_r | dns   | dig +short @resolver1.opendns.com myip.opendns.com -4  |
        | tnx       | https | https://tnx.nl/ip                                      |
        +-----------+-------+--------------------------------------------------------+

    It can be used for looping in tests, etc. like this::

        $ for method in $(psec utils myip methods -f value -c Method)
        > do
        >   echo "$method: $(psec utils myip --method $method)"
        > done
        akamai: 93.184.216.34
        amazon: 93.184.216.34
        google: 93.184.216.34
        icanhazip: 93.184.216.34
        infoip: 93.184.216.34
        opendns_h: 93.184.216.34
        opendns_r: 93.184.216.34
        tnx: 93.184.216.34
    """  # noqa

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'method',
            nargs='*',
            default=None
        )
        parser.epilog = QUOTA_WARNING
        return parser

    def take_action(self, parsed_args):
        columns = ('Method', 'Type', 'Source')
        data = []
        methods = (parsed_args.method
                   if len(parsed_args.method) > 0
                   else myip_methods.keys())

        for method, mechanics in sorted(myip_methods.items()):
            if method in methods:
                data.append((
                    method,
                    mechanics['func'](),
                    mechanics['arg']
                    ))
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
