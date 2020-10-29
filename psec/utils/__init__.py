# -*- coding: utf-8 -*-

"""
Utility functions.

Author: Dave Dittrich
URL: https://python_secrets.readthedocs.org.
"""

import argparse
import ipaddress
import json
import logging
import os
import random
import requests
import time
import psec.secrets
import psutil
import subprocess  # nosec
import sys
import textwrap

from anytree import Node
from anytree import RenderTree
from bs4 import BeautifulSoup
# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass
from cliff.command import Command
from cliff.lister import Lister
from collections import OrderedDict
from configobj import ConfigObj
from six.moves import input


AWS_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')

# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.

LOG = logging.getLogger(__name__)


def bell():
    if sys.stderr.isatty():
        sys.stderr.write('\a')
        sys.stderr.flush()


# https://stackoverflow.com/questions/7119630/in-python-how-can-i-get-the-file-system-of-a-given-file-path  # NOQA
def getmount(mypath):
    """Return the mount point for mypath."""
    path_ = os.path.realpath(os.path.abspath(mypath))
    while path_ != os.path.sep:
        if os.path.ismount(path_):
            return path_
        path_ = os.path.abspath(os.path.join(path_, os.pardir))
    return path_


def getmount_fstype(mypath):
    """Return the file system type for a specific mount path."""
    mountpoint = getmount(mypath)
    return get_fs_type(mountpoint)


def get_fs_type(mypath):
    """Return the file system type for mypath."""
    root_type = ''
    for part in psutil.disk_partitions():
        if part.mountpoint == os.path.sep:
            root_type = part.fstype
            continue
        if mypath.startswith(part.mountpoint):
            return part.fstype
    return root_type


def remove_other_perms(dst):
    """Make all files in path ``dst`` have ``o-rwx`` permissions."""
    # File permissions on Cygwin/Windows filesystems don't work the
    # same way as Linux. Don't try to change them.
    # TODO(dittrich): Is there a Better way to handle perms on Windows?
    fs_type = get_fs_type(dst)
    if fs_type in ['NTFS', 'FAT', 'FAT32']:
        msg = ('[-] {0} has file system type "{1}": '
               'skipping setting permissions').format(
                   dst, fs_type)
        LOG.info(msg)
    else:
        get_output(['chmod', '-R', 'o-rwx', dst])


def get_output(cmd=['echo', 'NO COMMAND SPECIFIED'],
               cwd=os.getcwd(),
               stderr=subprocess.STDOUT,
               shell=False):
    """Use subprocess.check_ouput to run subcommand"""
    output = subprocess.check_output(  # nosec
            cmd,
            cwd=cwd,
            stderr=stderr,
            shell=shell
        ).decode('UTF-8').splitlines()
    return output


def find(lst, key, value):
    """Find a dictionary entry from a list of dicts where the
    key identified by 'key' has the desired value 'value'."""
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


def prompt_options(options=[],
                   by_descr=True,
                   prompt="Select from the following options"):
    """Prompt the user for a string using an options array."""
    if 'Bullet' not in globals():
        raise RuntimeError('[-] can\'t use Bullet on Windows')
    try:
        if type(options[0]) is not dict:
            raise RuntimeError('options is not a list of dictionaries')
    except Exception as exc:
        print(str(exc))
    choices = ['<CANCEL>'] + [
                                opt['descr']
                                if by_descr
                                else opt['ident']
                                for opt in options
                             ]
    cli = Bullet(prompt='\n{0}'.format(prompt),
                 choices=choices,
                 indent=0,
                 align=2,
                 margin=1,
                 shift=0,
                 bullet="→",
                 pad_right=5)
    choice = cli.launch()
    if choice == "<CANCEL>":
        LOG.info('cancelled selection of choice')
        return None
    selected = psec.utils.find(options,
                               'descr' if by_descr else 'ident',
                               choice)
    # options[selected]
    # {'descr': 'DigitalOcean', 'ident': 'digitalocean'}
    try:
        return options[selected]['ident']
    except Exception as exc:  # NOQA
        return None


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


def default_environment(parsed_args=None):
    """Return the default environment for this cwd"""
    env_file = os.path.join(os.getcwd(),
                            '.python_secrets_environment')
    if parsed_args.unset:
        try:
            os.remove(env_file)
        except Exception as e:  # noqa
            LOG.info('no default environment was set')
        else:
            LOG.info('default environment unset')
    elif parsed_args.set:
        # Set default to specified environment
        default_env = parsed_args.environment
        if default_env is None:
            default_env = psec.secrets.SecretsEnvironment().environment()
        with open(env_file, 'w') as f:
            f.write(default_env)
        LOG.info('default environment set to "{}"'.format(
            default_env))


class MyIP(Command):
    """Get currently active internet routable IPv4 address."""

    log = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=cmd_name)
        # Function map
        self.myip_methods = {
            'opendns_resolver': self.myip_opendns_resolver,
            'opendns_com': self.myip_opendns_com,
            'whatismyip_host': self.myip_opendns_resolver,
        }

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        default_method = self.get_myip_methods()[0]
        parser.add_argument(
            '-M', '--method',
            action='store',
            dest='method',
            choices=self.get_myip_methods() + ['random'],
            type=lambda m: m if m != 'random' else None,
            default=default_method,
            help="Method to use for determining IP address " +
                 "(default: {})".format(default_method)
        )
        parser.add_argument(
            '-C', '--cidr',
            action='store_true',
            dest='cidr',
            default=False,
            help="Express IP address as CIDR block " +
                 "(default: False)"
        )
        parser.epilog = textwrap.dedent("""
          KNOWN LIMITATION: Does not support IPv6 at this point, just IPv4.
        """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('getting current internet source IP address')
        interface = ipaddress.ip_interface(
            self.get_myip(method=parsed_args.method))
        if parsed_args.cidr:
            print(str(interface.with_prefixlen))
        else:
            print(str(interface.ip))

    def get_myip_methods(self):
        """Return list of available method ids for getting IP address."""
        return [m for m in self.myip_methods.keys()]

    def get_myip(self, method='myip_opendns_resolver'):
        if method is None:
            method = random.choice(self.get_myip_methods())  # nosec
        func = self.myip_methods.get(method, lambda: None)
        if func is not None:
            LOG.debug('[+] determining IP address using ' +
                      'method "{}" '.format(method))
            return func()
        else:
            raise RuntimeError('Method "{}" '.format(method) +
                               'for obtaining IP address is ' +
                               'not implemented')

    @classmethod
    def myip_opendns_com(cls):
        URL = 'http://diagnostic.opendns.com/myip'
        page = requests.get(URL, stream=True)
        interface = ipaddress.ip_interface(page.text)
        return interface

    @classmethod
    def myip_opendns_resolver(cls):
        cmd = ['dig',
               '@resolver1.opendns.com',
               'ANY',
               'myip.opendns.com',
               '+short']
        output = get_output(cmd=cmd)
        interface = ipaddress.ip_interface(output[0])
        return interface

    @classmethod
    def myip_whatismyip_host(cls):
        """Use whatismyip.host to get IP address."""
        URL = 'http://whatismyip.host'
        page = requests.get(URL, stream=True)
        LOG.debug('[+] got page: "{}"'.format(page.text))
        soup = BeautifulSoup(page.text, 'html.parser')
        interface = None
        for div_ipshow in soup.findAll('div', {"class": "ipshow"}):
            LOG.debug('[+] found div "{}"'.format(div_ipshow.text))
            # TODO(dittrich): Only handles IPv4 addresses at the moment...
            try:
                (label, addr) = div_ipshow.text.split('\n')[1:3]
                if interface is None \
                        and label.lower() == 'your ip v4 address:':
                    interface = ipaddress.ip_interface(addr)
            except Exception as err:  # noqa
                pass
        return interface


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
#
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


class TfBackend(Command):
    """
    Enable Terraform backend support to move terraform.tfstate file
    out of current working directory into environment path.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--path',
            action='store_true',
            dest='path',
            default=False,
            help="Print path and exit (default: False)"
        )
        # tfstate = None
        # try:
        #     tfstate = os.path.join(self.app.secrets.environment_path(),
        #                            "terraform.tfstate")
        # except AttributeError:
        #     pass
        parser.epilog = textwrap.dedent("""
            TBD(dittrich): Write this...
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        e = psec.secrets.SecretsEnvironment(
                environment=self.app.options.environment)
        tmpdir = e.tmpdir_path()
        backend_file = os.path.join(os.getcwd(), 'tfbackend.tf')
        tfstate_file = os.path.join(tmpdir, 'terraform.tfstate')
        backend_text = textwrap.dedent("""\
            terraform {{
              backend "local" {{
              path = "{tfstate_file}"
              }}
            }}
            """.format(tfstate_file=tfstate_file))

        if parsed_args.path:
            self.log.debug('showing terraform state file path')
            print(tfstate_file)
        else:
            self.log.debug('setting up terraform backend')
            if os.path.exists(backend_file):
                LOG.debug('updating {}'.format(backend_file))
            else:
                LOG.debug('creating {}'.format(backend_file))
            with open(backend_file, 'w') as f:
                f.write(backend_text)


class TfOutput(Lister):
    """Retrieve current 'terraform output' results."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        tfstate = None
        try:
            tfstate = os.path.join(self.app.secrets.tmpdir_path(),
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
        if self.app_args.verbose_level > 1:
            # NOTE(dittrich): Not DRY, but spend time fixing later.
            self.log.info(' '.join(['terraform',
                                    'output',
                                    '-state={}'.format(tfstate),
                                    '-json']))
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


def atree(dir,
          print_files=True,
          outfile=None):
    """
    Produces the tree structure for the path specified on the command
    line. If output is specified (e.g., as sys.stdout) it will be used,
    otherwise a list of strings is returned.

    Uses anytree: https://anytree.readthedocs.io/en/latest/

    :param dir:
    :param print_files:
    :param outfile:
    :return: str
    """

    nodes = dict()
    nodes[dir] = Node(dir)
    root_node = nodes[dir]
    for root, dirs, files in os.walk(dir, topdown=True):
        if root not in nodes:
            nodes[root] = Node(root)
        for name in files:
            if print_files:
                nodes[os.path.join(root, name)] = \
                    Node(name, parent=nodes[root])
        for name in dirs:
            nodes[os.path.join(root, name)] = Node(name, parent=nodes[root])

    output = []
    for pre, fill, node in RenderTree(root_node):
        output.append((f'{ pre }{ node.name }'))
    if outfile is not None:
        for line in output:
            print(line, file=outfile)
    else:
        return output


class Timer(object):
    """
    Timer object usable as a context manager, or for manual timing.
    Based on code from http://coreygoldberg.blogspot.com/2012/06/python-timer-class-context-manager-for.html  # noqa

    As a context manager, do:

        from timer import Timer

        url = 'https://github.com/timeline.json'

        with Timer() as t:
            r = requests.get(url)

        print 'fetched %r in %.2f millisecs' % (url, t.elapsed*1000)

    """

    def __init__(self, task_description='elapsed time', verbose=False):
        self.verbose = verbose
        self.task_description = task_description
        self.laps = OrderedDict()

    def __enter__(self):
        """Record initial time."""
        self.start(lap="__enter__")
        if self.verbose:
            sys.stdout.write('{}...'.format(self.task_description))
            sys.stdout.flush()
        return self

    def __exit__(self, *args):
        """Record final time."""
        self.stop()
        backspace = '\b\b\b'
        if self.verbose:
            sys.stdout.flush()
            if self.elapsed_raw() < 1.0:
                sys.stdout.write(backspace + ':' + '{:.2f}ms\n'.format(
                    self.elapsed_raw() * 1000))
            else:
                sys.stdout.write(backspace + ': ' + '{}\n'.format(
                    self.elapsed()))
            sys.stdout.flush()

    def start(self, lap=None):
        """Record starting time."""
        t = time.time()
        first = None if len(self.laps) == 0 \
            else self.laps.iteritems().next()[0]
        if first is None:
            self.laps["__enter__"] = t
        if lap is not None:
            self.laps[lap] = t
        return t

    def lap(self, lap="__lap__"):
        """
        Records a lap time.
        If no lap label is specified, a single 'last lap' counter will be
        (re)used. To keep track of more laps, provide labels yourself.
        """
        t = time.time()
        self.laps[lap] = t
        return t

    def stop(self):
        """Record stop time."""
        return self.lap(lap="__exit__")

    def get_lap(self, lap="__exit__"):
        """Get the timer for label specified by 'lap'"""
        return self.lap[lap]

    def elapsed_raw(self, start="__enter__", end="__exit__"):
        """Return the elapsed time as a raw value."""
        return self.laps[end] - self.laps[start]

    def elapsed(self, start="__enter__", end="__exit__"):
        """
        Return a formatted string with elapsed time between 'start'
        and 'end' kwargs (if specified) in HH:MM:SS.SS format.
        """
        hours, rem = divmod(self.elapsed_raw(start, end), 3600)
        minutes, seconds = divmod(rem, 60)
        return "{:0>2}:{:0>2}:{:05.2f}".format(
            int(hours), int(minutes), seconds)


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
