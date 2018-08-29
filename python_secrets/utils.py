import ipaddress
import json
import logging
import os
import requests
import subprocess  # nosec

from cliff.command import Command
from cliff.lister import Lister
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
        cwd = os.getcwd()
        tfstate = os.path.join(cwd, 'terraform.tfstate')
        parser = super().get_parser(prog_name)
        parser.add_argument('tfstate', nargs='?', default=tfstate)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('getting terraform output')
        columns = ('Variable', 'Value')
        data = list()
        tfstate = parsed_args.tfstate
        if not os.path.exists(tfstate):
            raise RuntimeError('No terraform state file "{}"'.format(
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

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
