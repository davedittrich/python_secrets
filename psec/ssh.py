# -*- coding: utf-8 -*-

import argparse
import boto3
import fileinput
import json
import logging
import os
import pexpect
import re
import socket
import sys
import tempfile
import textwrap
import time

from cliff.command import Command
from jinja2 import Template


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
        ssh_hosts = json.dumps({'ssh_hosts': hosts})
        cmd = ['ansible-playbook',
               '--ask-become-pass',
               _ansible_verbose(verbose_level),
               '-e', "'{}'".format(ssh_hosts),
               '-e', 'remove_keys=true',
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


def _write_ssh_configd(ssh_config=None,
                       name="testing",
                       aws_privatekey_path=None,
                       public_ip=None,
                       public_dns=None):
    """
    Write an SSH configuration file snippet.
    
    This supports construction of a user's ``~/.ssh/config`` file using
    ``update-dotdee``.
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


class SSHConfig(Command):
    """
    Create an SSH configuration snippet for use by ``update-dotdee``.

    This snippet will reside in the directory ``~/.ssh/config.d/``
    and ``update-dotdee`` will be run after creating it to apply
    the new configuration for immediate use.
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
            raise RuntimeError('Must specify --public-ip and --public-dns')
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


class SSHKnownHostsAdd(Command):
    """
    Add public SSH keys to known_hosts file(s).

    This command will either extract SSH public host keys and fingerprints
    from a cloud service console output (either directly via an API, from
    standard input, or from saved output from instantiation of the cloud
    instance.)

    By default, the public keys are added to the system known_hosts file
    (which is not writeable by normal users) for added security. The file
    is manipulated indirectly using an embedded Ansible playbook.
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
                raise RuntimeError('Could not get-console-output ' +
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
                key_type = re.sub(r'(|)', '', fields[-1].lower())
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


class SSHKnownHostsRemove(Command):
    """
    Remove SSH keys from known_hosts file(s).
    
    This command indirectly manipulates the known hosts file
    using an embedded Ansible playbook.
    """  # noqa

    log = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=None)
        self.host = None
        self.hostname = None

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
        parser.add_argument('source',
                            nargs="?",
                            help="console output to process",
                            default=None)
        parser.epilog = textwrap.dedent("""
            """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('removing SSH known host keys')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        self.host = parsed_args.public_ip
        self.hostname = parsed_args.public_dns

        if self.host is None and self.hostname is not None:
            # TODO(dittrich): reverse lookup IP from hostname
            pass
        if self.hostname is None and self.host is not None:
            # TODO(dittrich): lookup hostname from IP
            try:
                self.hostname = socket.gethostbyaddr(self.host)[0]
            except Exception:
                pass
            pass

        _ansible_remove_hostkeys([i for i in [self.host, self.hostname]
                                  if i is not None],
                                 verbose_level=self.app_args.verbose_level)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
