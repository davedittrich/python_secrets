# -*- coding: utf-8 -*-

"""
Utility functions.

  Author: Dave Dittrich <dave.dittrich@gmail.com>

  URL: https://python_secrets.readthedocs.org.
"""

import logging
import os
import tempfile
import time
import psec.secrets
import psutil
import subprocess  # nosec
import sys

from anytree import Node
from anytree import RenderTree
# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass
from collections import OrderedDict
from ipwhois import IPWhois


# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.


logger = logging.getLogger(__name__)


def bell():
    """
    Output an ASCII BEL character to ``stderr``.
    """

    if sys.stderr.isatty():
        sys.stderr.write('\a')
        sys.stderr.flush()


# https://stackoverflow.com/questions/7119630/in-python-how-can-i-get-the-file-system-of-a-given-file-path  # noqa
def getmount(mypath):
    """
    Identifies the filesystem mount point for the partition containing ``mypath``.

    Args:
      mypath (str): Candidate path.

    Returns:
      string: The mount point for the filesystem partition containing ``path``.
    """  # noqa

    path_ = os.path.realpath(os.path.abspath(mypath))
    while path_ != os.path.sep:
        if os.path.ismount(path_):
            return path_
        path_ = os.path.abspath(os.path.join(path_, os.pardir))
    return path_


def getmount_fstype(mypath):
    """
    Identifies the file system type for a specific mount path.

    Args:
      mypath (str): Candidate path.

    Returns:
      string: File system type for partition containing ``mypath``.
    """

    mountpoint = getmount(mypath)
    return get_fs_type(mountpoint)


def get_fs_type(mypath):
    """
    Identifies the file system type for a specific mount path.

    Args:
      mypath (str): Candidate path.

    Returns:
      string: File system type for partition containing ``mypath``.
    """

    root_type = ''
    for part in psutil.disk_partitions():
        if part.mountpoint == os.path.sep:
            root_type = part.fstype
            continue
        if mypath.startswith(part.mountpoint):
            return part.fstype
    return root_type


def get_files_from_path(path=None):
    """
    Gets a list of absolute paths to one or more files associated with a path.

    If ``path`` is a directory, the files contained in it are returned,
    otherwise the path to the file is the only item in the list.

    Args:
      path (str): Candidate path.

    Returns:
      list: A list of one or more absolute file paths.
    """

    abspath = os.path.abspath(path)
    if os.path.isfile(abspath):
        files = [abspath]
    elif os.path.isdir(abspath):
        files = [
            os.path.join(abspath, fname)
            for fname in os.listdir(abspath)
        ]
    else:
        raise RuntimeError(f"[-] '{path}' must be a file or directory")
    return files


def get_netblock(ip=None):
    """
    Derives the CIDR netblocks for an IP via WHOIS lookup.

    Args:
      ip (str): IP address

    Returns:
      string: One or more CIDR blocks
    """

    ip = str(ip).split('/')[0] if '/' in str(ip) else ip
    obj = IPWhois(ip)
    results = obj.lookup_whois()
    return results['asn_cidr']


def remove_other_perms(dst):
    """
    Make all files in path ``dst`` have ``o-rwx`` permissions.

    NOTE: This does not work on file system types ``NTFS``, ``FAT``, or
    ``FAT32``. A log message will be produced when this is encountered.
    """
    # File permissions on Cygwin/Windows filesystems don't work the
    # same way as Linux. Don't try to change them.
    # TODO(dittrich): Is there a Better way to handle perms on Windows?
    fs_type = get_fs_type(dst)
    if fs_type in ['NTFS', 'FAT', 'FAT32']:
        msg = ('[-] {0} has file system type "{1}": '
               'skipping setting permissions').format(
                   dst, fs_type)
        logger.info(msg)
    else:
        get_output(['chmod', '-R', 'o-rwx', dst])


def get_output(cmd=['echo', 'NO COMMAND SPECIFIED'],
               cwd=os.getcwd(),
               stderr=subprocess.STDOUT,
               shell=False):
    """
    Uses ``subprocess.check_ouput()`` to run a sub-command.

    Args:
      cmd (list): Argument list
      cwd (str): Directory to use for current working directory by shell
      stderr (file handle): Where should ``stderr`` be directed? (default: ``subprocess.STDOUT``)
      shell (bool): Use a shell (default: ``FALSE``)

    Returns:
      list of str: Output from command
    """  # noqa

    output = subprocess.check_output(  # nosec
            cmd,
            cwd=cwd,
            stderr=stderr,
            shell=shell
        ).decode('UTF-8').splitlines()
    return output


def find(lst, key, value):
    """
    Searches a list of dictionaries by value of a specified key.

    Find the first item from a list of dicts where the key identified by
    ``key`` has the value specified by ``value``.

    Args:
      lst (list of dict): List of dictionaries to search
      key (str): Key to compare
      value (str): Value to find

    Returns:
      Index to the first entry with the matching value or ``None``
    """

    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None


def redact(string, redact=False):
    return "REDACTED" if redact else string


def require_options(options, *args):
    missing = [arg for arg in args if getattr(options, arg) is None]
    if missing:
        raise RuntimeError(
            f"[-] missing options: {' '.join(missing)}")
    return True


def prompt_options_list(options=[],
                        default=None,
                        prompt="Select from the following options"):
    """Prompt the user for a string using a list of options."""
    cancel = '<CANCEL>'
    if 'Bullet' not in globals():
        raise RuntimeError("[-] can't use Bullet on Windows")
    if not len(options) or type(options[0]) is not str:
        raise RuntimeError('[-] a list of options is required')
    if default is None:
        default = cancel
    else:
        # Remove the default from the list because it will
        # be added back as the first item.
        options = [i for i in options if i != default]
    choices = [default] + options
    cli = Bullet(prompt='\n{0}'.format(prompt),
                 choices=choices,
                 indent=0,
                 align=2,
                 margin=1,
                 shift=0,
                 bullet="→",
                 pad_right=5)
    choice = cli.launch()
    if default == cancel and choice == cancel:
        logger.info('[-] cancelled selection of choice')
        return None
    return choice


def prompt_options_dict(options=[],
                        by_descr=True,
                        prompt="Select from the following options"):
    """Prompt the user for a string using option dictionaries."""
    if 'Bullet' not in globals():
        raise RuntimeError("[-] can't use Bullet on Windows")
    try:
        if type(options[0]) is not dict:
            raise RuntimeError('[-] options is not a list of dictionaries')
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
        logger.info('[-] cancelled selection of choice')
        return None
    selected = psec.utils.find(options,
                               'descr' if by_descr else 'ident',
                               choice)
    # options[selected]
    # {'descr': 'DigitalOcean', 'ident': 'digitalocean'}
    try:
        return options[selected]['ident']
    except Exception as exc:  # noqa
        return None


# >> Issue: [B322:blacklist] The input method in Python 2 will read from
# standard input, evaluate and run the resulting string as python source code.
# This is similar, though in many ways worse, then using eval. On Python 2, use
# raw_input instead, input is safe in Python 3.
#    Severity: High   Confidence: High Location: psec/utils/__init__.py:200
#    More Info:
#    https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b322-input  # noqa

def prompt_string(prompt="Enter a value",
                  default=None):
    """Prompt the user for a string and return it"""
    _new = None
    while True:
        try:
            _new = str(input(f"{prompt}? [{str(default)}]: "))  # nosec
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
            logger.info('[-] no default environment was set')
        else:
            logger.info('[-] default environment unset')
    elif parsed_args.set:
        # Set default to specified environment
        default_env = parsed_args.environment
        if default_env is None:
            default_env = psec.secrets.SecretsEnvironment().environment()
        with open(env_file, 'w') as f:
            f.write(default_env)
        logger.info(f"[+] default environment set to '{default_env}'")


def safe_delete_file(
    file_name=None,
    passes=3,
    verbose=False
):
    if int(passes) < 1:
        passes = 1
    if file_name in ["", None]:
        raise RuntimeError('[-] file_name not specified')
    if not os.path.isfile(file_name):
        raise RuntimeError(f"[-] '{file_name}' is not a file")
    if verbose:
        logger.info(f"[+] removing '{file_name}'")
    with open(file_name, 'ba+', buffering=0) as fp:
        length = fp.tell()
    for i in range(passes):
        with open(file_name, 'br+', buffering=0) as fp:
            fp.seek(0)
            fp.write(os.urandom(length))
            fp.flush()
    mask_name = os.path.join(os.path.dirname(file_name),
                             os.path.basename(tempfile.mkstemp('')[1]))
    os.rename(file_name, mask_name)
    os.unlink(mask_name)


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


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
