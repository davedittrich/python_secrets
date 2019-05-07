# -*- coding: utf-8 -*-

import argparse
import boto3
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

# Delay variables for reading AWS console-output
_TRIES = 45
_DELAY = 5

# Ansible playbook for managing known_hosts file contents
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
          become: true
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
          become: true
          when: not remove_keys|bool

        - name: Fix file permissions on known_hosts file
          file:
            path: '{{ ssh_known_hosts_files.0 }}'
            mode: 0o644
          become: true
    """).encode('utf-8')  # noqa

SSH_CONFIG_TEMPLATE = textwrap.dedent("""\
    Host {{ shortname  }} {{ public_ip }} {{ public_dns }}
        Hostname {{ public_ip }}
        IdentityFile {{ aws_privatekey_path }}
        Port {{ port }}
        User {{ username }}
    \n
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


def _ansible_set_hostkeys(hostkeys,
                          debug=False,
                          ask_become_pass='--ask-become-pass',
                          verbose_level=1):
    """Use Ansible playbook to set SSH known host keys"""
    with tempfile.NamedTemporaryFile() as playbook:
        playbook.seek(0)
        playbook.write(REKEY_PLAYBOOK)
        playbook.flush()
        if verbose_level > 2:
            print(REKEY_PLAYBOOK, file=sys.stderr, flush=True)
        cmd = ['ansible-playbook',
               ask_become_pass,
               _ansible_verbose(verbose_level),
               '-e', "'{}'".format(hostkeys),
               playbook.name
               ]
        ansible = pexpect.spawnu(
            " ".join([arg for arg in cmd]))
        ansible.interact()
        if ansible.isalive():
            raise RuntimeError('Ansible did not exit gracefully.')


def _ansible_remove_hostkeys(hosts,
                             debug=False,
                             ask_become_pass='--ask-become-pass',
                             verbose_level=1):
    """Use Ansible playbook to remove SSH known host keys"""
    with tempfile.NamedTemporaryFile() as playbook:
        playbook.seek(0)
        playbook.write(REKEY_PLAYBOOK)
        if verbose_level > 2:
            print(REKEY_PLAYBOOK, file=sys.stderr, flush=True)
        playbook.flush()
        ssh_hosts = json.dumps({'ssh_hosts': hosts})
        cmd = ['ansible-playbook',
               ask_become_pass,
               _ansible_verbose(verbose_level),
               '-e', "'{}'".format(ssh_hosts),
               '-e', 'remove_keys=true',
               playbook.name,
               ]
        ansible = pexpect.spawnu(
            " ".join([arg for arg in cmd]))
        ansible.interact()
        # Short delay because randomly this causes an exception
        # to be thrown. (Am I doing something wrong?)
        time.sleep(3)
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
                       public_dns=None,
                       verbose_level=1):
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
        if verbose_level > 2:
            print(output_text, file=sys.stderr, flush=True)

def get_instance_id_from_source(source=None):
    """Try to extract the instance ID from the source file name"""
    filename = getattr(source, 'name')
    instance_id = None
    try:
        offset = filename.find('-console-output.txt')
        if offset != -1:
            instance_id = filename[0:-offset]
    except Exception as e:  # noqa
        pass
    return instance_id


class PublicKeys(object):
    """Class for managing SSH public keys."""

    log = logging.getLogger(__name__)

    def __init__(self,
                 public_ip=None,
                 public_dns=None,
                 instance_id=None,
                 debug=False):
        self.console_output = None
        self.public_ip = public_ip
        self.public_dns = public_dns
        self.hostkey = list()
        self.hostfingerprint = list()
        self.instance_id = instance_id
        self.debug = debug
        self.client = None

    def get_public_ip(self):
        """Return the host IP address"""
        return self.public_ip

    def get_public_dns(self):
        """Return the hostname"""
        return self.public_dns

    def set_instance_id_from_source(self, source=None):
        """Set instance ID attribute from the source file name"""
        self.instance_id = get_instance_id_from_source(source=source)
        return self.instance_id

    def update_instance_description(self, instance_id=None):
        """
        Return specific information about a specific AWS instance, or
        the first instance found to be running.

        This method only finds the first running instance in the list
        of reservations (which may include recently terminanted
        instances.)
        """

        # TODO(dittrich): Make this capable of handling multi-instance stacks
        # Return a list or dictionary of multiple public_ip/public_dns sets.
        if self.client is None:
            self.client = boto3.client('ec2')
        stack_list = self.client.describe_instances().get('Reservations')
        if len(stack_list) == 0:
            raise RuntimeError("No running instances found")
        if instance_id is None:
            for stack in stack_list:
                for instance in stack['Instances']:
                    state = instance['State']['Name']
                    if state != 'running':
                        self.log.debug('Ignoring {} '.format(state) +
                                       'instance {}'.format(
                                            instance['InstanceId']))
                    else:
                        self.log.debug('Found running ' +
                                       'instance {}'.format(
                                            instance['InstanceId']))
                        self.public_ip = instance.get(
                            'PublicIpAddress', None)
                        self.public_dns = instance.get(
                            'PublicDnsName', None)
                        break
        else:
            for stack in stack_list:
                for instance in stack['Instances']:
                    if instance['InstanceId'] == instance_id:
                        self.public_ip = instance.get('PublicIpAddress', None)
                        self.public_dns = instance.get('PublicDnsName', None)
        return {'public_ip': self.public_ip,
                'public_dns': self.public_dns}

    def process_aws_console_output(self, instance_id=None):
        if self.client is None:
            self.client = boto3.client('ec2')
        result_dict = self.update_instance_description(instance_id=instance_id)
        tries_left = _TRIES
        response = None
        while tries_left > 0:
            response = self.client.get_console_output(
                InstanceId=self.instance_id,
            )
            if 'Output' in response:
                break
            time.sleep(_DELAY)
            tries_left -= 1
            if self.debug:
                self.log.debug('attempt {} '.format(_TRIES - tries_left) +
                               'to get console-log failed')
        if tries_left == 0 or response is None:
            raise RuntimeError('Could not get-console-output ' +
                               'in {} seconds'.format(_TRIES * _DELAY) +
                               '\nCheck instance-id or try again.')
        self.console_output = response['Output'].splitlines()
        self.extract_keys()

    def process_saved_console_output(self, source=None):
        """Get console output from stdin or file"""
        if source is None:
            raise RuntimeError('No console-output was found')
        self.console_output = [line.strip() for line in source]
        self.extract_keys()

    def extract_keys(self):
        """Extract public keys from console-output text"""
        if self.console_output is None:
            raise RuntimeError('No console output to process')
        in_fingerprints = False
        in_pubkeys = False
        fields = list()
        for line in self.console_output:
            if line.startswith('ec2: '):
                line = line[5:].strip()
            else:
                line = line.strip()
            if line.find(' Host: ') >= 0:
                _host = line.split(': ')[1]
                if _host != "":
                    self.public_ip = _host
                    try:
                        self.public_dns = \
                            socket.gethostbyaddr(self.public_ip)[0]
                    except Exception:
                        pass
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
                if self.debug:
                    self.log.info('fingerprint: {}'.format(fingerprint))
            elif in_pubkeys:
                fields = line.split(' ')
                key = "{} {}".format(fields[0], fields[1])
                self.hostkey.append(key)
                if self.debug:
                    self.log.info('pubkey: {}'.format(key))

    def get_hostfingerprint_list(self):
        """Return the hostfingerprint list"""
        return self.hostfingerprint

    def get_hostkey_list_as_json(self):
        """
        Output JSON with host key material in a dictionary with
        key 'ssh_host_public_key' for use in Ansible playbook.
        """
        keylist = list()
        if self.public_ip is None or self.public_dns is None:
            raise RuntimeError('No host IP or name found')
        for key in self.hostkey:
            if self.public_ip is not None:
                keylist.append("{} {}".format(self.public_ip, key))
            if self.public_dns is not None:
                keylist.append("{} {}".format(self.public_dns, key))
        return json.dumps({'ssh_host_public_keys': keylist})

    def get_hostkey_list(self):
        """Return the hostkey list"""
        return self.hostkey


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
        parser.add_argument(
            '--show-config',
            action='store_true',
            dest='show_config',
            default=False,
            help="Show the SSH configuration on standard output and exit."
        )
        parser.epilog = textwrap.dedent("""
            Use ``-vvv`` to see the configuration file in the terminal
            command line output.
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
        if parsed_args.show_config:
            # TODO(dittrich): finish this...
            pass
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
    from a cloud service console output (either directly via an API or
    or from saved output from instantiation of the cloud instance.)

    By default, the public keys are added to the system ``known_hosts``
    file (``/etc/ssh/ssh_known_hosts``, which is not writeable by normal
    users) for added security. The file is manipulated indirectly using
    an embedded Ansible playbook.
    """  # noqa

    log = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=None)
        self.public_ip = None
        self.public_dns = None

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
            '--show-playbook',
            action='store_true',
            dest='show_playbook',
            default=False,
            help="Show the playbook on standard output and exit."
        )
        parser.add_argument(
            '--ask-become-pass',
            action='store_const',
            const='--ask-become-pass',
            default='',
            help='Ask for sudo password for Ansible privilege escalation ' +
                 '(default: do not ask)'
        )
        parser.add_argument('source',
                            nargs="?",
                            type=argparse.FileType('r'),
                            help="console output to process",
                            default=None)  # sys.stdin)
        parser.epilog = textwrap.dedent("""
            Use ``--show-playbook`` to just see the Ansible playbook without
            running it. Use ``-vvv`` to see the Ansible playbook while it is
            being applied.

            The Ansible playbook uses ``become`` to elevate privileges. On
            Linux systems, this usually relies on ``sudo``. If plays in the
            playbook fail with ``"module_stderr": "sudo: a password is required"``
            in the message, you will need to use the ``--ask-become-pass``
            option to be prompted for your password.

            NOTE: Because of the use of Ansible, with the potential need for
            using ``sudo``, you cannot pipe console-output text into ``psec``
            using I/O redirection or piping. The following exception will be
            thrown::

              ...
              File "[...]/site-packages/pexpect/pty_spawn.py", line 783, in interact
                mode = tty.tcgetattr(self.STDIN_FILENO)
              termios.error: (25, 'Inappropriate ioctl for device')
              ...
            \n
            If this happens, save the console output to a file and pass its
            name as a command line argument.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('extracting/adding SSH known host keys')
        if parsed_args.show_playbook:
            print('[+] Playbook for managing SSH known_hosts files')
            print(REKEY_PLAYBOOK.decode('utf-8'))
            return True

        # TODO(dittrich): NOT DRY warning.
        # Replicates code from 'ssh known-hosts add'

        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()

        # Get the instance_id from command line option, or
        # from console output file name. Avoid a conflict.
        if (parsed_args.instance_id is not None and
           not (parsed_args.public_ip is None or parsed_args.public_dns is None)):  # noqa
            raise RuntimeError('--instance-id cannot be used with ' +
                               'either --public-ip or --public-dns')
        if parsed_args.source is not None:
            instance_id = get_instance_id_from_source(
                source=parsed_args.source)
            if parsed_args.instance_id is not None:
                if parsed_args.instance_id != instance_id:
                    raise RuntimeError('--instance-id given does not match '
                                       'name of source console log')
        else:
            instance_id = parsed_args.instance_id

        public_ip = parsed_args.public_ip
        public_dns = parsed_args.public_dns
        public_keys = PublicKeys(public_ip=public_ip,
                                 public_dns=public_dns,
                                 instance_id=instance_id,
                                 debug=self.app.options.debug)
        if parsed_args.source is not None:
            public_keys.process_saved_console_output(parsed_args.source)
        elif instance_id is not None:
            public_keys.process_aws_console_output()
        hostkeys_as_json_string = public_keys.get_hostkey_list_as_json()
        if self.app.options.debug:
            _ansible_debug(hostkeys_as_json_string)

        _ansible_set_hostkeys(hostkeys_as_json_string,
                              debug=self.app.options.debug,
                              ask_become_pass=parsed_args.ask_become_pass,
                              verbose_level=self.app_args.verbose_level)


class SSHKnownHostsRemove(Command):
    """
    Remove SSH keys from known_hosts file(s).

    This command indirectly manipulates the known hosts file
    using an embedded Ansible playbook.
    """  # noqa

    log = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=None)
        self.public_ip = None
        self.public_dns = None

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
            '--ask-become-pass',
            action='store_const',
            const='--ask-become-pass',
            default='',
            help='Ask for sudo password for Ansible privilege escalation ' +
                 '(default: do not ask)'
        )
        parser.add_argument('source',
                            nargs="?",
                            type=argparse.FileType('r'),
                            help="console output to process",
                            default=None)  # sys.stdin)
        parser.add_argument(
            '--show-playbook',
            action='store_true',
            dest='show_playbook',
            default=False,
            help="Show the playbook on standard output and exit."
        )
        parser.epilog = textwrap.dedent("""
            Use ``--show-playbook`` to just see the Ansible playbook without
            running it. Use ``-vvv`` to see the Ansible playbook while it is
            being applied.

            The Ansible playbook uses ``become`` to elevate privileges. On
            Linux systems, this usually relies on ``sudo``. If plays in the
            playbook fail with ``"module_stderr": "sudo: a password is required"``
            in the message, you will need to use the ``--ask-become-pass``
            option to be prompted for your password.

            NOTE: Because of the use of Ansible, with the potential need for
            using ``sudo``, you cannot pipe console-output text into ``psec``
            using I/O redirection or piping. The following exception will be
            thrown::

              ...
              File "[...]/site-packages/pexpect/pty_spawn.py", line 783, in interact
                mode = tty.tcgetattr(self.STDIN_FILENO)
              termios.error: (25, 'Inappropriate ioctl for device')
              ...
            \n
            If this happens, save the console output to a file and pass its
            name as a command line argument.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('removing SSH known host keys')
        if parsed_args.show_playbook:
            print('[+] Playbook for managing SSH known_hosts files')
            print(REKEY_PLAYBOOK.decode('utf-8'))
            return True

        # TODO(dittrich): NOT DRY warning. Replicates code from 'ssh known-hosts add'

        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()

        # Get the instance_id from command line option, or
        # from console output file name. Avoid a conflict.
        if (parsed_args.instance_id is not None and
           not (parsed_args.public_ip is None or parsed_args.public_dns is None)):  # noqa
            raise RuntimeError('--instance-id cannot be used with ' +
                               'either --public-ip or --public-dns')
        if parsed_args.source is not None:
            instance_id = get_instance_id_from_source(
                source=parsed_args.source)
            if parsed_args.instance_id is not None:
                if parsed_args.instance_id != instance_id:
                    raise RuntimeError('--instance-id given does not match '
                                       'name of source console log')
        else:
            instance_id = parsed_args.instance_id

        public_ip = parsed_args.public_ip
        public_dns = parsed_args.public_dns
        public_keys = PublicKeys(public_ip=public_ip,
                                 public_dns=public_dns,
                                 instance_id=instance_id,
                                 debug=self.app.options.debug)
        if parsed_args.source is not None:
            public_keys.process_saved_console_output(parsed_args.source)
        elif instance_id is not None:
            public_keys.process_aws_console_output()
        hostkeys_as_json_string = public_keys.get_hostkey_list_as_json()
        if self.app.options.debug:
            _ansible_debug(hostkeys_as_json_string)

        _ansible_remove_hostkeys([i for i in [public_keys.get_public_ip(),
                                              public_keys.get_public_dns()]
                                  if i is not None],
                                 debug=self.app.options.debug,
                                 ask_become_pass=parsed_args.ask_become_pass,
                                 verbose_level=self.app_args.verbose_level)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
