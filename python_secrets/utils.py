import ipaddress
import json
import logging
import os
import requests
import subprocess  # nosec
import textwrap

from cliff.command import Command
from cliff.lister import Lister
from os import listdir, sep
from os.path import abspath, basename, isdir
from six.moves import input


OPENDNS_URL = 'https://diagnostic.opendns.com/myip'
# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.


def get_output(cmd=['echo', 'NO COMMAND SPECIFIED'],
               stderr=subprocess.STDOUT,
               shell=False):
    """Use subprocess.check_ouput to run subcommand"""
    output = subprocess.check_output(  # nosec
            cmd,
            stderr=stderr,
            shell=shell
        ).decode('UTF-8').splitlines()
    return output


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None


def redact(string, redact=False):
    return "REDACTED" if redact else string


def require_options(options, *args):
    missing = [arg for arg in args if getattr(options, arg) is None]
    if missing:
        raise RuntimeError('Missing options: %s' % ' '.join(missing))
    return True


def prompt_string(prompt="Enter a value",
                  default=None):
    """Prompt the user for a string and return it"""
    _new = None
    while True:
        try:
            _new = str(input("{}? [{}]: ".format(prompt, str(default))))
            break
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue
        except KeyboardInterrupt:
            break
    return default if _new in [None, ''] else _new


class MyIP(Command):
    """Get current internet routable source address."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '-C', '--cidr',
            action='store_true',
            dest='cidr',
            default=False,
            help="Express IP address as CIDR block " +
                 "(default: False)"
        )
        parser.epilog = textwrap.dedent("""
        """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('getting current internet source IP address')
        r = requests.get(OPENDNS_URL, stream=True)
        interface = ipaddress.ip_interface(r.text)
        if parsed_args.cidr:
            print(str(interface.with_prefixlen))
        else:
            print(str(interface.ip))

# The TfOutput Lister assumes `terraform output` structured as
# shown here:
#
# $ terraform output -state=xgt/terraform.tfstate
# xgt = {
#   instance_user = ec2-user
#   privatekey_path = /home/dittrich/.ssh/xgt.pem
#   public_dns = ec2-52-27-37-238.us-west-2.compute.amazonaws.com
#   public_ip = 52.27.37.238
#   spot_bid_state = [active]
#   spot_bid_status = [fulfilled]
#   spot_instance_id = [i-06590cf97d79bdfd9]
# }
#
# $ terraform output -state=xgt/terraform.tfstate -json
# {
#     "xgt": {
#         "sensitive": false,
#         "type": "map",
#         "value": {
#             "instance_user": "ec2-user",
#             "privatekey_path": "/home/dittrich/.ssh/xgt.pem",
#             "public_dns": "ec2-52-27-37-238.us-west-2.compute.amazonaws.com",
#             "public_ip": "52.27.37.238",
#             "spot_bid_state": [
#                 "active"
#             ],
#             "spot_bid_status": [
#                 "fulfilled"
#             ],
#             "spot_instance_id": [
#                 "i-06590cf97d79bdfd9"
#             ]
#         }
#     }
# }


class TfOutput(Lister):
    """Retrieve current 'terraform output' results."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('tfstate',
                            nargs='?',
                            default=None,
                            help="Path to Terraform state file " +
                                 "(default: None)"
                            )
        parser.epilog = textwrap.dedent("""
        If the ``tfstate`` argument is not provided, this command will attempt to   # noqa
        search for a ``terraform.tfstate`` file in (1) the active environment's     # noqa
        secrets storage directory (see ``environments path``), or (2) the current   # noqa
        working directory. The former is documented preferred location for storing  # noqa
        this file, since it will contain secrets that _should not_ be stored in     # noqa
        a source repository directory to avoid potential leaking of those secrets.  # noqa

        .. code-block:: console

            $ psec environments path
            /Users/dittrich/.secrets/python_secrets

        ..
        """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('getting terraform output')
        columns = ('Variable', 'Value')
        data = list()
        tfstate = parsed_args.tfstate
        if tfstate is None:
            base = 'terraform.tfstate'
            tfstate = os.path.join(self.app.secrets.environment_path(), base)
            if not os.path.exists(tfstate):
                tfstate = os.path.join(os.getcwd(), base)
            if not os.path.exists(tfstate):
                raise RuntimeError('No terraform state file specified')
        if not os.path.exists(tfstate):
            raise RuntimeError('File does not exist: "{}"'.format(
                tfstate)
            )
        # >> Issue: [B607:start_process_with_partial_path] Starting a process with a partial executable path  # noqa
        #    Severity: Low   Confidence: High
        #    Location: python_secrets/utils.py:152
        p = subprocess.Popen(['terraform',  # nosec
                              'output',
                              '-state={}'.format(tfstate),
                              '-json'],
                             env=dict(os.environ),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)
        jout, err = p.communicate()
        dout = json.loads(jout.decode('UTF-8'))
        for prefix in dout.keys():
            for k, v in dout[prefix]['value'].items():
                data.append(["{}_{}".format(prefix, k), v])
        return columns, data


def tree(dir, padding='', print_files=True, isLast=False, isFirst=True):
    """
    Prints the tree structure for the path specified on the command line

    Modified code from tree.py written by Doug Dahms
    https://stackoverflow.com/a/36253753

    :param dir:
    :param padding:
    :param print_files:
    :param isLast:
    :param isFirst:
    :return:
    """

    if isFirst:
        print(padding[:-1] + dir)
    else:
        if isLast:
            print(padding[:-1] + str('└── ') + basename(abspath(dir)))
        else:
            print(padding[:-1] + str('├── ') + basename(abspath(dir)))
    files = []
    if print_files:
        files = listdir(dir)
    else:
        files = [x for x in listdir(dir) if isdir(dir + sep + x)]
    if not isFirst:
        padding = padding + '   '
    files = sorted(files, key=lambda s: s.lower())
    count = 0
    last = len(files) - 1
    for i, file in enumerate(files):
        count += 1
        path = dir + sep + file
        isLast = (i == last)
        if isdir(path):
            if count == len(files):
                if isFirst:
                    tree(path, padding, print_files, isLast, False)
                else:
                    tree(path, padding + ' ', print_files, isLast, False)
            else:
                tree(path, padding + '│', print_files, isLast, False)
        else:
            if isLast:
                print(padding + '└── ' + file)
            else:
                print(padding + '├── ' + file)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
