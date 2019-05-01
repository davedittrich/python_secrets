# -*- coding: utf-8 -*-

import argparse
import boto3
import fileinput
import ipaddress
import json
import logging
import os
import pexpect
import re
import requests
import socket
import subprocess  # nosec
import sys
import textwrap
import time
import tempfile

from cliff.command import Command
from cliff.lister import Lister
from configobj import ConfigObj
from jinja2 import Template
from os import listdir, sep
from os.path import abspath, basename, isdir
from six.moves import input


AWS_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
OPENDNS_URL = 'https://diagnostic.opendns.com/myip'

REKEY_PLAYBOOK = textwrap.dedent("""\
    ---

    - hosts: '{{ host|default("127.0.0.1") }}'
      connection: '{{ ((host is not defined) or ("127.0.0.1" in host))|ternary("local","smart") }}'
      gather_facts: '{{ ((host is not defined) or ("127.0.0.1" in host))|ternary("false","true") }}'
      become: yes
      vars:
        remove_keys: false
        ansible_python_interpreter: "python3"

      tasks:
        - name: Assert ssh_hosts is defined when removing
          assert:
            that:
            - ssh_hosts is defined
          when: remove_keys|bool

        - name: Debug ssh_hosts variable
          debug:
            var: ssh_hosts
          when: remove_keys|bool

        - name: Assert ssh_host_public_keys is defined when adding
          assert:
            that:
              - ssh_host_public_keys is defined
          when: not remove_keys|bool

        - name: Define ssh_known_hosts_files
          set_fact:
            ssh_known_hosts_files: '{{ ssh_known_hosts_files|default([]) + [ item ] }}'
          with_items:
            - /etc/ssh/ssh_known_hosts
           #- /root/.ssh/known_hosts
           #- '{{ lookup("pipe", "echo ~{{ ansible_user }}/.ssh/known_hosts") }}'

        - name: Remove old SSH host keys
          local_action: known_hosts state=absent path={{ item.0 }} host={{ item.1 }}
          ignore_errors: True
          with_nested:
            - '{{ ssh_known_hosts_files }}'
            - '{{ ssh_hosts }}'
          when: remove_keys|bool

        - name: Ensure SSH host keys are present
          known_hosts:
            state: present
            path: '{{ item.0 }}'
            key: '{{ item.1 }}'
            host: '{{ item.1.split(" ")[0].split(",")[0] }}'
          with_nested:
            - '{{ ssh_known_hosts_files }}'
            - '{{ ssh_host_public_keys }}'
          ignore_errors: yes
          when: not remove_keys|bool

        - name: Fix file permissions on known_hosts file
          file:
            path: '{{ ssh_known_hosts_files.0 }}'
            mode: 0o644
    """).encode('utf-8')  # noqa

SSH_CONFIG_TEMPLATE = textwrap.dedent("""\
    Host {{ shortname  }} {{ public_ip }} {{ public_dns }}
        Hostname {{ public_ip }}
        IdentityFile {{ aws_privatekey_path }}
        Port {{ port }}
        User {{ username }}
    """)

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


def _ansible_verbose(verbose_level=1):
    """
    Return an ansible verbose flag for a given Cliff app verbose
    level to pass along desired verbosity intent.
    """
    flag = ''
    if verbose_level > 1:
        flag = '-{}'.format("v" * (verbose_level - 1))
    return flag


def _ansible_set_hostkeys(hostkeys, debug=False, verbose_level=1):
    """Use Ansible playbook to set SSH known host keys"""
    with tempfile.NamedTemporaryFile() as playbook:
        playbook.seek(0)
        playbook.write(REKEY_PLAYBOOK)
        playbook.flush()
        cmd = ['ansible-playbook',
               '--ask-become-pass',
               _ansible_verbose(verbose_level),
               '-e', "'{}'".format(hostkeys),
               playbook.name
               ]
        ansible = pexpect.spawnu(
            " ".join([arg for arg in cmd]))
        ansible.interact()
        if ansible.isalive():
            raise RuntimeError('Ansible did not exit gracefully.')


def _ansible_remove_hostkeys(hosts, debug=False, verbose_level=1):
    """Use Ansible playbook to remove SSH known host keys"""
    with tempfile.NamedTemporaryFile() as playbook:
        playbook.seek(0)
        playbook.write(REKEY_PLAYBOOK)
        playbook.flush()
        cmd = ['ansible-playbook',
               '--ask-become-pass',
               _ansible_verbose(verbose_level),
               '-e', 'remove_keys=true',
               '-e', '\'ssh_hosts="{}"\''.format(str(list(hosts))),
               playbook.name,
               ]
        ansible = pexpect.spawnu(
            " ".join([arg for arg in cmd]))
        ansible.interact()
        if ansible.isalive():
            raise RuntimeError('Ansible did not exit gracefully.')


def _ansible_debug(hostkeys):
    """Debug Ansible"""
    cmd = ['ansible',
           '-e', "'{}'".format(hostkeys),
           '-m', 'debug',
           '-a', 'var=vars',
           'all'
           ]
    output, exitstatus = pexpect.runu(
        " ".join([arg for arg in cmd]),
        withexitstatus=1)
    print(output, file=sys.stdout, flush=True)
    if exitstatus != 0:
        raise RuntimeError('Ansible error ' +
                           '(see stdout and stderr above)')
    # p = subprocess.Popen(cmd,
    #                      env=dict(os.environ),
    #                      stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE,
    #                      shell=False)
    # p_out, p_err = p.communicate()
    # print(p_out.decode('utf-8'), file=sys.stdout, flush=True)
    # if p.returncode != 0:
    #     print(p_err.decode('utf-8'), file=sys.stderr, flush=True)
    #     raise RuntimeError('Ansible error (see stdout and stderr above)')


def _write_ssh_configd(ssh_config=None,
                       name="testing",
                       aws_privatekey_path=None,
                       public_ip=None,
                       public_dns=None):
    """
    Write an SSH configuration snippet for use by
    update-dotdee to construct ~/.ssh/config.
    """
    template_vars = dict()
    template_vars['aws_privatekey_path'] = aws_privatekey_path
    template_vars['port'] = 22
    template_vars['username'] = 'ec2-user'
    template_vars['shortname'] = name
    template_vars['public_ip'] = public_ip
    template_vars['public_dns'] = public_dns
    for k, v in template_vars.items():
        if v is None or v == '':
            raise RuntimeError('Variable "{}" must be defined'.format(k))
    config_dir_path = ssh_config + '.d'
    if not os.path.exists(config_dir_path):
        raise RuntimeError('Directory {}'.format(config_dir_path) +
                           'for update-dotdee does not exist')
    config_file_path = os.path.join(config_dir_path, name)
    with open(config_file_path, 'w') as f:
        template = Template(SSH_CONFIG_TEMPLATE)
        output_text = template.render(dict(template_vars))
        f.writelines(output_text)


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
    """Set credentials from saved secrets for use by AWS CLI.

    This command directly manipulates the AWS CLI "credentials" INI-style
    file.  The AWS CLI does not support non-interactive manipulation of
    the credentials file, so this hack is used to do this. Be aware that
    this might cause some problems (though it shouldn't, since the file
    is so simple.)

    Use the --user option to select a specific user, otherwise "default"
    is used.
    """

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
            """)
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


class SSHConfig(Command):
    """
    Create an SSH configuration snippet for use by 'update-dotdee' for
    generating the user's ~/.ssh/config file. This snippet will reside
    in the directory ~/.ssh/config.d/.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--public-ip',
            action='store',
            dest='public_ip',
            default=None,
            help='IP address of host (default: None)'
        )
        parser.add_argument(
            '--public-dns',
            action='store',
            dest='public_dns',
            default=None,
            help='DNS name of host (default: None)'
        )
        parser.epilog = textwrap.dedent("""
            """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('creating SSH configuration snippet')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        if parsed_args.public_ip is None or parsed_args.public_dns is None:
            raise RuntimeError('Must specify --public_ip and --public_dns')
        _aws_privatekey_path = \
            self.app.secrets.get_secret('aws_privatekey_path')
        home = os.path.expanduser('~')
        ssh_config = os.path.join(home, '.ssh/config')
        _write_ssh_configd(ssh_config=ssh_config,
                           name=self.app.secrets._environment,
                           aws_privatekey_path=_aws_privatekey_path,
                           public_ip=parsed_args.public_ip,
                           public_dns=parsed_args.public_dns)
        output, exitstatus = pexpect.runu(
            'update-dotdee {}'.format(ssh_config),
            withexitstatus=1)
        if exitstatus == 0:
            if self.app_args.verbose_level >= 1:
                print(output, file=sys.stdout, flush=True)
        else:
            print(output, file=sys.stdout, flush=True)
            raise RuntimeError('update-dotdee error ' +
                               '(see stdout and stderr above)')


class SSHKnownHosts(Command):
    """
    Manage SSH known_hosts file contents. This command will either extract
    SSH known hosts keys and fingerprints and add keys to the system
    "known_hosts file, or it will remove keys from that file.
    This command indirectly manipulates the host's SSH "known_hosts"
    file using an Ansible playbook.
    """  # noqa

    log = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=None)
        self.host = None
        self.hostname = None
        self.hostkey = list()
        self.hostfingerprint = list()

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--public-ip',
            action='store',
            dest='public_ip',
            default=None,
            help='IP address of host (default: None)'
        )
        parser.add_argument(
            '--public-dns',
            action='store',
            dest='public_dns',
            default=None,
            help='DNS name of host (default: None)'
        )
        parser.add_argument(
            '--instance-id',
            action='store',
            dest='instance_id',
            default=None,
            help='instance ID for getting direct AWS ' +
                 'console output (default: None)'
        )
        parser.add_argument(
            '--remove-keys',
            action='store_true',
            dest='remove_keys',
            default=False,
            help="Remove known_hosts keys " +
                 "(default: False)"
        )
        parser.add_argument('source',
                            nargs="?",
                            help="console output to process",
                            default=None)
        parser.epilog = textwrap.dedent("""
            If no source argument is specified, standard input will be
            read.
            """)
        return parser

    def take_action(self, parsed_args):
        if parsed_args.remove_keys:
            self.log.debug('removing SSH known host keys')
        else:
            self.log.debug('extracting/adding SSH known host keys')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        _TRIES = 45
        _DELAY = 5
        in_fingerprints = False
        in_pubkeys = False
        fields = list()
        console_output = ""
        self.host = parsed_args.public_ip
        # If the public_ip was not set on the command line, wait
        # until we see if it is provided in the console output
        # that will be parsed for SSH public keys and fingerprints.
        self.hostname = parsed_args.public_dns
        if parsed_args.instance_id is not None:
            response = dict()
            client = boto3.client('ec2')
            tries_left = _TRIES
            while tries_left > 0:
                response = client.get_console_output(
                    InstanceId=parsed_args.instance_id,
                )
                if 'Output' in response:
                    break
                time.sleep(_DELAY)
                tries_left -= 1
                if self.app.options.debug:
                    self.log.debug('attempt {} '.format(_TRIES - tries_left) +
                                   'to get console-log failed')
            if tries_left == 0:
                raise RuntimeError('Could not get-console-output '+
                                   'in {} seconds'.format(_TRIES * _DELAY) +
                                   '\nCheck instance-id or try again.')
            console_output = response['Output'].splitlines()
        else:
            if parsed_args.source is not None:
                console_output = [line.strip() for line
                                  in fileinput.input(parsed_args.source)]
        for line in console_output:
            if line.startswith('ec2: '):
                line = line[5:].strip()
            else:
                line = line.strip()
            if line.find(' Host: ') >= 0:
                self.host = line.split(': ')[1]
            elif line.find('BEGIN SSH HOST KEY FINGERPRINTS') >= 0:
                in_fingerprints = True
                continue
            elif line.find('END SSH HOST KEY FINGERPRINTS') >= 0:
                in_fingerprints = False
                continue
            elif line.find('BEGIN SSH HOST KEY KEYS') >= 0:
                in_pubkeys = True
                continue
            elif line.find('END SSH HOST KEY KEYS') >= 0:
                in_pubkeys = False
                continue
            if in_fingerprints:
                fields = line.split(' ')
                key_type = re.sub('\(|\)', '', fields[-1].lower())
                fingerprint = "{} {}".format(key_type, fields[1])
                self.hostfingerprint.append(fingerprint)
                if self.app.options.debug:
                    self.log.info('fingerprint: {}'.format(fingerprint))
            elif in_pubkeys:
                fields = line.split(' ')
                key = "{} {}".format(fields[0], fields[1])
                self.hostkey.append(key)
                if self.app.options.debug:
                    self.log.info('pubkey: {}'.format(key))
        # Now try to ensure we also have a host name to ensure
        # known_hosts entries are present for it.
        if self.hostname is None:
            try:
                self.hostname = socket.gethostbyaddr(self.host)[0]
            except Exception:
                pass
        hostkeys_as_json_string = self._dump_hostkeys_to_json()
        if self.app.options.debug:
            _ansible_debug(hostkeys_as_json_string)
        if parsed_args.remove_keys:
            _ansible_remove_hostkeys([i for i in [self.host, self.hostname]
                                      if i is not None],
                                     verbose_level=self.app_args.verbose_level)
        else:
            _ansible_set_hostkeys(hostkeys_as_json_string,
                                  debug=self.app.options.debug,
                                  verbose_level=self.app_args.verbose_level)

    def _dump_hostkeys_to_json(self):
        """
        Output JSON with host key material in a dictionary with
        key 'ssh_host_public_key' for use in Ansible playbook.
        """
        keylist = list()
        if self.host is None or self.hostname is None:
            raise RuntimeError('No host IP or name found')
        for key in self.hostkey:
            if self.host is not None:
                keylist.append("{} {}".format(self.host, key))
            if self.hostname is not None:
                keylist.append("{} {}".format(self.hostname, key))
        return json.dumps({'ssh_host_public_keys': keylist})


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
