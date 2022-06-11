# -*- coding: utf-8 -*-

"""
Utility functions.

  Author: Dave Dittrich <dave.dittrich@gmail.com>

  URL: https://python_secrets.readthedocs.org.
"""

# Standard imports
import argparse
import logging
import os
import random
import subprocess  # nosec
import stat
import sys
import tempfile
import time


# External imports
import ipaddress
import requests
import psutil

from anytree import (
    Node,
    RenderTree,
)
# Workaround until bullet has Windows missing 'termios' fix.
# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
try:
    from bullet import (
        Bullet,
        YesNo,
    )
except ModuleNotFoundError:
    pass
from bs4 import BeautifulSoup
from collections import OrderedDict
from ipwhois import IPWhois
from pathlib import Path
from shutil import (
    copy,
    copytree,
)

# Local imports
from psec.exceptions import (
    BasedirNotFoundError,
    InvalidBasedirError,
    InvalidDescriptionsError,
    # SecretNotFoundError,
)


logger = logging.getLogger(__name__)

DEFAULT_UMASK = 0o077
MAX_UMASK = 0o777
DEFAULT_MODE = 0o700
DEFAULT_FILE_MODE = 0o600
MARKER = '.psec'
BASEDIR_BASENAME = '.secrets' if os.sep == '/' else 'secrets'
SECRETS_FILE = 'secrets.json'
SECRETS_DESCRIPTIONS_DIR = f'{os.path.splitext(SECRETS_FILE)[0]}.d'


class CustomFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """
    Custom class to control arparse help output formatting.
    """


class Memoize:
    """Memoize(fn) - an instance which acts like fn but memoizes its arguments.

       Will only work on functions with non-mutable arguments. Hacked to assume
       that argument to function is whether to cache or not, allowing all
       secrets of a given type to be set to the same value.
    """

    def __init__(self, fn):
        self.fn = fn
        self.memo = {}

    def __call__(self, *args):
        if args[0] is True:
            return self.fn(*args)
        if args not in self.memo:
            self.memo[args] = self.fn(*args)
        return self.memo[args]


def natural_number(value):
    """
    Tests for a natural number.

    Args:
      value: The value to test

    Returns:
      A boolean indicating whether the value is a natural number or not.
    """

    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            f"[-] '{value}' is not a positive integer")
    return ivalue


# TODO(dittrich): Improve this?
def _is_default(a, b):
    """
    Return "Yes" or "No" depending on whether e is the default
    environment or not.
    """
    return "Yes" if a == b else "No"


def get_local_default_file(cwd=None):
    """Returns the path to the local identifier file."""
    # TODO(dittrich): May need to do this differently to support
    # Windows file systems.
    if cwd is None:
        cwd = os.getcwd()
    return Path(cwd) / '.python_secrets_environment'


def save_default_environment(
    environment=None,
    cwd=None
):
    """Save environment identifier to local file for defaulting."""
    env_file = get_local_default_file(cwd=cwd)
    with open(env_file, 'w') as f_out:
        f_out.write('{0}\n'.format(str(environment)))
    return True


def clear_saved_default_environment(cwd=None):
    """Remove saved default environment file."""
    env_file = get_local_default_file(cwd=cwd)
    if os.path.exists(env_file):
        os.remove(env_file)
        return True
    else:
        return False


def get_saved_default_environment(cwd=None):
    """Return environment ID value saved in local file or None."""
    env_file = get_local_default_file(cwd=cwd)
    saved_default = None
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            saved_default = f.read().replace('\n', '')
    return saved_default


def is_secrets_basedir(basedir=None, raise_exception=True):
    """
    Validate secrets base directory by presence of a marker file.

    Returns False if the directory either does not exist or does not
    contain the expected marker file, or True otherwise.
    """
    result = False
    if basedir is None:
        if raise_exception:
            raise RuntimeError("[-] no basedir was specified")
    basedir_path = Path(basedir)
    marker_path = Path(basedir) / MARKER
    if not basedir_path.exists():
        if raise_exception:
            raise BasedirNotFoundError(basedir=basedir)
    elif not marker_path.exists():
        if raise_exception:
            raise InvalidBasedirError(basedir=basedir)
    else:
        result = True
    return result


def get_default_secrets_basedir():
    """
    Return the default secrets base directory path.
    """
    default_basedir = Path.home() / BASEDIR_BASENAME
    return Path(
        os.getenv('D2_SECRETS_BASEDIR', default_basedir)
    )


def secrets_basedir_create(
    basedir=None,
    mode=DEFAULT_MODE,
):
    """Create secrets root directory"""
    if basedir is None:
        raise RuntimeError("[-] a base directory is required")
    secrets_basedir = Path(basedir)
    secrets_basedir.mkdir(
        parents=True,
        mode=mode,
        exist_ok=True
    )
    marker = secrets_basedir / MARKER
    marker.touch(exist_ok=True)
    marker.chmod(mode=DEFAULT_FILE_MODE)
    return secrets_basedir


def ensure_secrets_basedir(
    secrets_basedir=None,
    allow_create=False,
    allow_prompt=False,
    verbose_level=1,
):
    """
    Ensure that the secrets basedir exists.

    If the path is within the user's home directory, it is OK to
    create the directory automatically if it does not exist. This was
    the original behavior. If the path does exist and contains file,
    but does not have the special marker, that will be considered
    an error the user needs to resolve.

    For paths that lie outside the user's home directory, the user
    must explicitly confirm that it is OK to create the directory
    by responding to prompts (when possible) or by using the
    `--init` option flag or `psec init` command.
    """
    if secrets_basedir is None:
        secrets_basedir = get_default_secrets_basedir()
    homedir = str(Path.home())
    if allow_create is None:
        allow_create = str(secrets_basedir).startswith(homedir)
    valid_basedir = False
    try:
        valid_basedir = is_secrets_basedir(
            basedir=secrets_basedir,
            raise_exception=True,
        )
    except BasedirNotFoundError as err:
        if verbose_level > 0:
            logger.info(str(err))
        if not allow_create:
            if allow_prompt:
                client = YesNo(
                    f"create directory '{secrets_basedir}'? ",
                    default='n'
                )
                result = client.launch()
                if not result:
                    sys.exit("[!] cancelled creating '%s'" % secrets_basedir)
            else:
                sys.exit(
                    "[-] add the '--init' flag or use 'psec init' "
                    "to initialize secrets storage"
                )
    except InvalidBasedirError as err:
        if not allow_create:
            sys.exit(str(err))
    if not valid_basedir:
        secrets_basedir_create(basedir=secrets_basedir)
        if verbose_level >= 1:
            logger.info(
                "[+] initialized secrets storage in '%s'",
                secrets_basedir
            )
    # else:
    #     if verbose_level >= 1:
    #         logger.info(
    #             "[+] secrets storage already initialized in '%s'",
    #             secrets_basedir
    #         )
    return Path(secrets_basedir)


def get_default_environment(cwd=None):
    """
    Return the default environment identifier.

    There are multiple ways for a user to specify the environment
    to use for python_secrets commands. Some of these involve
    explicit settings (e.g., via command line option, a
    saved value in the current working directory, or an
    environment variable) or implicitly from the name of the
    current working directory.
    """

    #  NOTE(dittrich): I know this code has multiple return points
    #  but it is simpler and easier to understand this way.
    #
    # Highest priority is inhereted environment variable.
    environment = os.getenv('D2_ENVIRONMENT', None)
    if environment is not None:
        return environment
    #
    # Next is saved file in current working directory.
    if cwd is None:
        cwd = os.getcwd()
    local_default = get_saved_default_environment(cwd=cwd)
    if local_default not in ['', None]:
        return local_default
    #
    # Lowest priority is the directory path basename.
    return os.path.basename(cwd)


def copyanything(src, dst):
    """Copy anything from src to dst."""
    try:
        copytree(src, dst, dirs_exist_ok=True)
    except FileExistsError as e:  # noqa
        pass
    except OSError as err:
        # TODO(dittrich): This causes a pylint error
        # Not sure what test cases would trigger this, or best fix.
        if err.errno == os.errno.ENOTDIR:  # type: ignore
            copy(src, dst)
        else:
            raise
    finally:
        remove_other_perms(dst)


def copydescriptions(src: Path, dst: Path):
    """
    Just copy the descriptions portion of an environment
    directory from src to dst.
    """

    if not dst.suffix == '.d':
        raise InvalidDescriptionsError(
            msg=f"[-] destination '{dst}' is not a descriptions ('.d') directory"  # noqa
        )
    # Ensure destination directory exists.
    dst.mkdir(exist_ok=True)
    if src.suffix == '.d' and not src.is_dir():
        raise InvalidDescriptionsError(
            msg=f"[-] source '{src}' is not a descriptions ('.d') directory"  # noqa
        )
    for descr_file in [f for f in src.iterdir() if f.suffix == '.json']:
        src_text = descr_file.read_text(encoding='utf-8')
        dst_file = dst / descr_file.name
        dst_file.write_text(src_text, encoding='utf-8')
    remove_other_perms(dst)


def umask(value):
    """Set umask."""
    if value.lower().find("o") < 0:
        raise argparse.ArgumentTypeError(
            'value ({}) must be expressed in '
            'octal form (e.g., "0o077")')
    ivalue = int(value, base=8)
    if ivalue < 0 or ivalue > MAX_UMASK:
        raise argparse.ArgumentTypeError(
            f"value ({ value }) must be between 0 and 0o777"
        )
    return ivalue


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
        if str(mypath).startswith(part.mountpoint):
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


def get_environment_paths(basedir=None):
    """
    Return sorted list of valid environment paths found in `basedir`.
    """
    basedir = (
        get_default_secrets_basedir() if basedir is None
        else Path(basedir)
    )
    results = list()
    for item in sorted(basedir.iterdir()):
        if is_valid_environment(item):
            results.append(item)
    return results


def is_valid_environment(env_path, verbose_level=1):
    """
    Check to see if this looks like a valid environment directory.

    Args:
      env_path: Path to candidate directory to test.
      verbose_level: Verbosity level (pass from app args)

    Returns:
      A boolean indicating whether the directory appears to be a valid
      environment directory or not based on contents including a
      'secrets.json' file or a 'secrets.d' directory.
    """
    environment = os.path.split(env_path)[1]
    contains_expected = False
    YAML_SECRETS_FILE = str(SECRETS_FILE).replace('json', 'yml')
    yaml_files = []
    for root, directories, filenames in os.walk(env_path):
        if (
            SECRETS_FILE in filenames
            or SECRETS_DESCRIPTIONS_DIR in directories
        ):
            contains_expected = True
        if YAML_SECRETS_FILE in filenames:
            yaml_files.append(Path(root) / YAML_SECRETS_FILE)
        if root.endswith(SECRETS_DESCRIPTIONS_DIR):
            yaml_files.extend([
                os.path.join(root, filename)
                for filename in filenames
                if filename.endswith('.yml')
            ])
    for filename in yaml_files:
        if verbose_level > 1:
            logger.warning("[!] found '%s'", filename)
    is_valid = (
        os.path.exists(env_path)
        and contains_expected
        and len(yaml_files) == 0
    )
    if len(yaml_files) > 0 and verbose_level > 0:
        logger.warning(
            "[!] environment '%s' needs conversion (see 'psec utils yaml-to-json --help')",  # noqa
            environment)
    if not is_valid and verbose_level > 1:
        logger.warning(
            "[!] environment directory '%s' exists but looks incomplete",
            env_path)
    return is_valid


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


def permissions_check(
    basedir='.',
    verbose_level=0,
):
    """Check for presense of pernicious overly-permissive permissions."""
    # File permissions on Cygwin/Windows filesystems don't work the
    # same way as Linux. Don't try to change them.
    # TODO(dittrich): Is there a Better way to handle perms on Windows?
    fs_type = get_fs_type(basedir)
    if fs_type in ['NTFS', 'FAT', 'FAT32']:
        msg = (
            f"[-] {basedir} has file system type '{fs_type}': "
            "skipping permissions check"
        )
        logger.info(msg)
        return
    any_other_perms = stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
    for root, dirs, files in os.walk(basedir, topdown=True):
        for name in files:
            path = os.path.join(root, name)
            try:
                st = os.stat(path)
                perms = st.st_mode & 0o777
                open_perms = (perms & any_other_perms) != 0
                if (open_perms and verbose_level >= 1):
                    print(
                        f"[!] file '{path}' is mode {oct(perms)}",
                        file=sys.stderr
                    )
            except OSError:
                pass
            for name in dirs:
                path = os.path.join(root, name)
                try:
                    st = os.stat(path)
                    perms = st.st_mode & 0o777
                    open_perms = (perms & any_other_perms) != 0
                    if (open_perms and verbose_level >= 1):
                        print(
                            (
                                f"[!] directory '{path}' is mode "
                                f"{oct(perms)}"
                            ),
                            file=sys.stderr
                        )
                except OSError:
                    pass


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


def prompt_options_list(options=None,
                        default=None,
                        prompt="Select from the following options"):
    """Prompt the user for a string using a list of options.

    The options will be one of the following:

    '*' - Any user input
    'A,*' - 'A', or any user input.
    'A,B' - Only choices are 'A' or 'B'.

    """
    if 'Bullet' not in globals():
        raise RuntimeError("[-] can't use Bullet on Windows")
    if (
        len(options) == 0
        or not isinstance(options[0], str)
    ):
        raise RuntimeError('[-] a list of options is required')
    cancel = '<CANCEL>'
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


def prompt_options_dict(options=None,
                        by_descr=True,
                        prompt="Select from the following options"):
    """
    Prompt the user for a string using option dictionaries.

    These dictionaries map a descriptive name to an identifier::

        {'descr': 'DigitalOcean', 'ident': 'digitalocean'}


    """
    if 'Bullet' not in globals():
        raise RuntimeError("[-] can't use Bullet on Windows")
    if options is None:
        raise RuntimeError('[-] no options specified')
    if not isinstance(options[0], dict):
        raise RuntimeError('[-] options is not a list of dictionaries')
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
    selected = find(options,
                    'descr' if by_descr else 'ident',
                    choice)
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
        logger.info("[+] removing '%s'", file_name)
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


def secrets_tree(
    env=None,
    outfile=None
):
    """
    Produces the tree structure for groups and secrets in an environment.

    If output is specified (e.g., as sys.stdout) it will be used,
    otherwise a list of strings is returned.

    Uses anytree: https://anytree.readthedocs.io/en/latest/

    :param environment_dir:
    :param outfile:
    :return: str
    """

    nodes = dict()
    env_name = str(env)
    nodes[env_name] = Node(env_name)
    root_node = nodes[env_name]
    for group in sorted(env.get_groups()):
        group_name = os.path.join(env_name, group)
        nodes[group_name] = Node(group, parent=root_node)
        for variable in sorted(env.get_items_from_group(group)):
            nodes[os.path.join(group_name, variable)] = \
                Node(variable, parent=nodes[group_name])

    output = []
    for pre, fill, node in RenderTree(root_node):
        output.append((f'{ pre }{ node.name }'))
    if outfile is not None:
        for line in output:
            print(line, file=outfile)
    else:
        return output


def show_current_value(variable=None):
    """Pretty-print environment variable (if set)."""
    value = os.getenv(variable, None)
    return f" ('{value}')" if value is not None else ''


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


def myip_http(arg=None):
    """Use an HTTP service that only returns IP address."""
    # Return type if no argument for use in Lister.
    if arg is None:
        return 'https'
    page = requests.get(arg, stream=True)
    soup = BeautifulSoup(page.text, 'html.parser')
    if page.status_code != 200:
        raise RuntimeError(
            f"[-] error: {page.reason}\n{soup.body.text}")
    logger.debug('[-] got page: "%s"', page.text)
    interface = ipaddress.ip_interface(str(soup).strip())
    return interface


def myip_resolver(arg=None):
    """Use DNS resolver to get IP address."""
    # Return type if no argument for use in Lister.
    if arg is None:
        return 'dns'
    output = get_output(cmd=arg.split(" "))
    # Clean up output
    result = str(output[0]).replace('"', '')
    try:
        interface = ipaddress.ip_interface(result)
    except TypeError:
        interface = None
    return interface


# Function map. (See epilog help text for MyIP.)
myip_methods = {
    'akamai': {
        'arg': 'dig +short @ns1-1.akamaitech.net ANY whoami.akamai.net',
        'func': myip_resolver
    },
    'amazon': {
        'arg': 'https://checkip.amazonaws.com',
        'func': myip_http,
    },
    'google': {
        'arg': 'dig +short @ns1.google.com TXT o-o.myaddr.l.google.com',
        'func': myip_resolver,
    },
    'opendns_h': {
        'arg': 'https://diagnostic.opendns.com/myip',
        'func': myip_http,
    },
    'opendns_r': {
        'arg': 'dig +short @resolver1.opendns.com myip.opendns.com -4',
        'func': myip_resolver,
    },
    'icanhazip': {
        'arg': 'https://icanhazip.com/',
        'func': myip_http,
    },
    'infoip': {
        'arg': 'https://api.infoip.io/ip',
        'func': myip_http,
    },
    'tnx': {
        'arg': 'https://tnx.nl/ip',
        'func': myip_http,
    }
}


def get_myip_methods(include_random=False):
    """Return list of available method ids for getting IP address."""
    methods = list(myip_methods.keys())
    # For argparse choices, set True
    if include_random:
        methods.append('random')
    return methods


def get_myip(method='random'):
    """Return current routable source IP address."""
    methods = get_myip_methods()
    if method == 'random':
        method = random.choice(methods)  # nosec
    elif method not in methods:
        raise RuntimeError(
            f"[-] method '{method}' for obtaining IP address is "
            "not implemented")
    func = myip_methods[method].get('func')
    logger.debug("[+] determining IP address using '%s'", method)
    arg = myip_methods[method].get('arg')
    ip = str(func(arg=arg))
    if len(ip) == 0 or ip is None:
        raise RuntimeError(
            f"[-] method '{method}' failed to get an IP address")
    return ip


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
