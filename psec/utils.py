# -*- coding: utf-8 -*-

import argparse
import ipaddress
import json
import logging
import os
import requests
import subprocess  # nosec
import textwrap

from cliff.command import Command
from cliff.lister import Lister
from configobj import ConfigObj
from os import listdir, sep
from os.path import abspath, basename, isdir
from six.moves import input


AWS_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
OPENDNS_URL = 'https://diagnostic.opendns.com/myip'

# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.

LOG = logging.getLogger(__name__)


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
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
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

# Pulumi output:
# $ pulumi stack output --json
# {
#   "instance_id": "i-06a01c878aa51b66c",
#   "instance_user": "ec2-user",
#   "privatekey_path": "/home/dittrich/.ssh/xgt.pem",
#   "public_dns": "ec2-34-220-229-93.us-west-2.compute.amazonaws.com",
#   "public_ip": "34.220.229.93",
#   "subnet_id": "subnet-0e642669",
#   "vpc_id": "vpc-745d6b13"
# }


class TfOutput(Lister):
    """Retrieve current 'terraform output' results."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        tfstate = None
        try:
            tfstate = os.path.join(self.app.secrets.environment_path(),
                                   "terraform.tfstate")
        except AttributeError:
            pass
        parser.add_argument('tfstate',
                            nargs='?',
                            default=tfstate,
                            help="Path to Terraform state file " +
                                 "(default: {})".format(tfstate)
                            )
        parser.epilog = textwrap.dedent("""
            If the ``tfstate`` argument is not provided, this command will
            attempt to search for a ``terraform.tfstate`` file in (1) the
            active environment's secrets storage directory (see ``environments
            path``), or (2) the current working directory. The former is
            documented preferred location for storing this file, since it
            will contain secrets that *should not* be stored in a source
            repository directory to avoid potential leaking of those secrets.

            .. code-block:: console

                $ psec environments path
                /Users/dittrich/.secrets/psec

            ..
            """)  # noqa
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
        #    Location: psec/utils.py:152
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


class SetAWSCredentials(Command):
    """Set credentials from saved secrets for use by AWS CLI."""

    # See https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html  # noqa

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-U', '--user',
            action='store',
            dest='user',
            default='default',
            help='IAM User who owns credentials (default: "default")'
        )
        parser.epilog = textwrap.dedent("""
            This command directly manipulates the AWS CLI "credentials" INI-style
            file.  The AWS CLI does not support non-interactive manipulation of
            the credentials file, so this hack is used to do this. Be aware that
            this might cause some problems (though it shouldn't, since the file
            is so simple)::

                [default]
                aws_access_key_id = [ Harm to Ongoing Matter ]
                aws_secret_access_key = [        HOM           ]
            \n
            For simple use cases, you will not need to switch between different
            users.  The default is to use the AWS convention of ``default``
            as seen in the example above.  If you do need to support multiple
            users, the ``--user`` option will allow you to specify the user.

            See also:

              * https://aws.amazon.com/cli/
              * https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html
            \n
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('setting AWS CLI IAM user credentials')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        required_vars = ['aws_access_key_id', 'aws_secret_access_key']
        config = ConfigObj(AWS_CONFIG_FILE)
        for v in required_vars:
            try:
                cred = self.app.secrets.get_secret(v)
            except Exception as err:  # noqa
                raise
            config[parsed_args.user][v] = cred
        config.write()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
