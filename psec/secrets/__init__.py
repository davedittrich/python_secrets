# -*- coding: utf-8 -*-

"""
'secrets' subcommands and related classes.

Author: Dave Dittrich
URL: https://python_secrets.readthedocs.org.
"""

import argparse
import base64
import binascii
import hashlib
import json
import logging
import os
import psec.utils
import psec.environments
import random
import re
import secrets
import stat
import sys

import uuid

from collections import OrderedDict
from numpy.random import bytes as np_random_bytes
# >> Issue: [B404:blacklist] Consider possible security implications associated with run module.  # noqa
#    Severity: Low   Confidence: High
#    Location: psec/secrets.py:21
#    More Info: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess  # noqa
from shutil import copy
from shutil import copytree
from shutil import Error

from xkcdpass import xkcd_password as xp

from psec.utils import get_files_from_path

# This module relies in part on features from the xkcdpass module.
#
# Copyright (c) 2011 - 2019, Steven Tobin and Contributors.
# All rights reserved.
#
# https://github.com/redacted/XKCD-password-generator

BOOLEAN_OPTIONS = [
    {'descr': 'True', 'ident': 'true'},
    {'descr': 'False', 'ident': 'false'},
]
DEFAULT_SIZE = 18
SECRET_TYPES = [
        OrderedDict({
            'Type': 'password',
            'Description': 'Simple (xkcd) password string',
            'Generable': True}),
        OrderedDict({
            'Type': 'string',
            'Description': 'Simple string',
            'Generable': False}),
        OrderedDict({
            'Type': 'boolean',
            'Description': 'Boolean (\'true\'/\'false\')',
            'Generable': False}),
        OrderedDict({
            'Type': 'crypt_6',
            'Description': 'crypt() SHA512 (\'$6$\')',
            'Generable': True}),
        OrderedDict({
            'Type': 'token_hex',
            'Description': 'Hexadecimal token',
            'Generable': True}),
        OrderedDict({
            'Type': 'token_urlsafe',
            'Description': 'URL-safe token',
            'Generable': True}),
        OrderedDict({
            'Type': 'consul_key',
            'Description': '16-byte BASE64 token',
            'Generable': True}),
        OrderedDict({
            'Type': 'sha1_digest',
            'Description': 'DIGEST-SHA1 (user:pass) digest',
            'Generable': True}),
        OrderedDict({
            'Type': 'sha256_digest',
            'Description': 'DIGEST-SHA256 (user:pass) digest',
            'Generable': True}),
        OrderedDict({
            'Type': 'zookeeper_digest',
            'Description': 'DIGEST-SHA1 (user:pass) digest',
            'Generable': True}),
        OrderedDict({
            'Type': 'uuid4',
            'Description': 'UUID4 token',
            'Generable': True}),
        OrderedDict({
            'Type': 'random_base64',
            'Description': 'Random BASE64 token',
            'Generable': True})
        ]
SECRET_ATTRIBUTES = [
    'Variable',
    'Group',
    'Type',
    'Export',
    'Prompt',
    'Options'
]
DEFAULT_MODE = 0o710
# XKCD password defaults
# See: https://www.unix-ninja.com/p/your_xkcd_passwords_are_pwned
WORDS = 4
MIN_WORDS_LENGTH = 3
MAX_WORDS_LENGTH = 6
MIN_ACROSTIC_LENGTH = 6
MAX_ACROSTIC_LENGTH = 6
DELIMITER = '.'


logger = logging.getLogger(__name__)


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


def copyanything(src, dst):
    """Copy anything from src to dst."""
    try:
        copytree(src, dst)
    except FileExistsError as e:  # noqa
        pass
    except OSError as err:
        if err.errno == os.errno.ENOTDIR:
            copy(src, dst)
        else:
            raise
    finally:
        psec.utils.remove_other_perms(dst)


def copydescriptions(src, dst):
    """
    Just copy the descriptions portion of an environment
    directory from src to dst.
    """

    if not dst.endswith('.d'):
        raise RuntimeError(
            f"[-] destination '{dst}' is not a descriptions "
            "('.d') directory")
    # Ensure destination directory exists.
    os.makedirs(dst, exist_ok=True)
    errors = []
    try:
        if src.endswith('.d') and os.path.isdir(src):
            copytree(src, dst)
        else:
            raise RuntimeError(
                f"[-] source '{src}' is not a descriptions "
                "('.d') directory")
    except OSError as err:
        errors.append((src, dst, str(err)))
    # catch the Error from the recursive copytree so that we can
    # continue with other files
    except Error as err:
        errors.extend(err.args[0])
    if errors:
        raise Error(errors)
    psec.utils.remove_other_perms(dst)


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
    contains_expected = False
    for root, directories, filenames in os.walk(env_path):
        if 'secrets.json' in filenames or 'secrets.d' in directories:
            contains_expected = True
    is_valid = os.path.exists(env_path) and contains_expected
    if not is_valid and verbose_level > 1:
        logger.warning(
            f"[!] environment directory '{env_path}' exists"
            "but is empty")
    return is_valid


class SecretsEnvironment(object):
    """
    Class for handling secrets environment metadata.

    Provides an interface to the directory contents for a secrets
    environment, including groups descriptions, a tmp/ directory,
    and any other required directories.

      Typical usage example::

          se = SecretsEnvironment(environment='env_name')


    Attributes:
        environment: Name of the environment.
        secrets_basedir: Base directory path to environment's storage.
        secrets_file: File name for storing secrets (defaults to 'secrets.json').
        create_root: Controls whether the root directory is created on first use.
        defer_loading: Don't load values (just initialize attributes).
        export_env_vars: Export all variables to the environment.
        preserve_existing: Don't over-write existing environment variables.
        env_var_prefix: Prefix to apply to all exported environment variables.
        source: Directory path from which to clone a new environment.
        verbose_level: Verbosity level (pass from app args).
    """  # noqa

    LOG = logging.getLogger(__name__)

    def __init__(self,
                 environment=None,
                 secrets_basedir=None,
                 secrets_file=os.getenv('D2_SECRETS_BASENAME',
                                        'secrets.json'),
                 create_root=True,
                 defer_loading=True,
                 export_env_vars=False,
                 preserve_existing=False,
                 env_var_prefix=None,
                 source=None,
                 verbose_level=1):
        self._changed = False
        if environment is not None:
            self._environment = environment
        else:
            self._environment = psec.environments.default_environment()
        self._secrets_file = secrets_file
        self._secrets_basedir = secrets_basedir
        self._verbose_level = verbose_level
        # Ensure root directory exists in which to create secrets
        # environments?
        if not self.secrets_basedir_exists():
            if create_root:
                self.secrets_basedir_create()
            else:
                raise RuntimeError(
                    f"[-] directory '{self.secrets_basedir()}' "
                    "does not exist and create_root=False")
        self._secrets_descriptions = f"{os.path.splitext(self._secrets_file)[0]}.d"  # noqa
        self.export_env_vars = export_env_vars
        self.preserve_existing = preserve_existing

        # When exporting environment variables, include one that specifies the
        # environment from which these variables were derived. This also works
        # around a limitation in Ansible where the current working directory
        # from which "ansible" was run. (The D2 lookup_plugin/python_secrets.py
        # script needs to communicate this back to python_secrets in order for
        # it's .python_secrets_environment file to be used to identify the
        # proper environment.)

        if self.export_env_vars is True:
            os.environ['PYTHON_SECRETS_ENVIRONMENT'] = self._environment

        self.env_var_prefix = env_var_prefix
        # Secrets attribute maps; anything else throws exception
        for a in SECRET_ATTRIBUTES:
            setattr(self, a, OrderedDict())
        if source is not None:
            self.clone_from(source)
            self.read_secrets_descriptions()
        self._secrets = OrderedDict()
        self._descriptions = OrderedDict()

    def __str__(self):
        """Produce string representation of environment identifier"""
        return str(self._environment)

    def environment(self):
        """Returns the environment identifier."""
        return self._environment

    @property
    def verbose_level(self):
        """Returns the verbosity level."""
        return self._verbose_level

    def changed(self):
        """Return boolean reflecting changed secrets."""
        return self._changed

    @classmethod
    def permissions_check(cls, basedir='.', verbose_level=0):
        """Check for presense of perniscious overly-permissive permissions."""
        # File permissions on Cygwin/Windows filesystems don't work the
        # same way as Linux. Don't try to change them.
        # TODO(dittrich): Is there a Better way to handle perms on Windows?
        fs_type = psec.utils.get_fs_type(basedir)
        if fs_type in ['NTFS', 'FAT', 'FAT32']:
            msg = (f"[-] {basedir} has file system type '{fs_type}': "
                   "skipping permissions check")
            cls.LOG.info(msg)
            return False
        any_other_perms = stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
        for root, dirs, files in os.walk(basedir, topdown=True):
            for name in files:
                path = os.path.join(root, name)
                try:
                    st = os.stat(path)
                    perms = st.st_mode & 0o777
                    open_perms = (perms & any_other_perms) != 0
                    if (open_perms and verbose_level >= 1):
                        print(f"[!] file '{path}' is mode {oct(perms)}",
                              file=sys.stderr)
                except OSError:
                    pass
                for name in dirs:
                    path = os.path.join(root, name)
                    try:
                        st = os.stat(path)
                        perms = st.st_mode & 0o777
                        open_perms = (perms & any_other_perms) != 0
                        if (open_perms and verbose_level >= 1):
                            print((
                                    f"[!] directory '{path}' is mode "
                                    f"{oct(perms)}"
                                  ),
                                  file=sys.stderr)
                    except OSError:
                        pass

    # TODO(dittrich): FIX Cere call
    def secrets_descriptions_dir(self):
        """Return the path to the drop-in secrets description directory"""
        _env = self._environment
        if not _env:
            return self.secrets_basedir()
        else:
            return os.path.join(self.secrets_basedir(),
                                self.secrets_basename().replace('.json', '.d'))

    def secrets_basename(self):
        """Return the basename of the current secrets file"""
        return os.path.basename(self._secrets_file)

    def secrets_basedir(self, init=False):
        """
        Returns the directory path root for secrets storage and definitions.

        When more than one environment is being used, a single top-level
        directory in the user's home directory is the preferred location.
        This function checks to see if such a directory exists, and if
        so defaults to that location.

        If the environment variable "D2_SECRETS_BASEDIR" is set, that location
        is used instead.
        """
        if self._secrets_basedir is None:
            _home = os.path.expanduser('~')
            _secrets_subdir = os.path.join(
                _home, 'secrets' if '\\' in _home else '.secrets')
            self._secrets_basedir = os.getenv('D2_SECRETS_BASEDIR',
                                              _secrets_subdir)
            if not os.path.exists(self._secrets_basedir) and init:
                self.secrets_basedir_create()
        return self._secrets_basedir

    def secrets_basedir_exists(self):
        """Return whether secrets root directory exists"""
        _secrets_basedir = self.secrets_basedir()
        return os.path.exists(_secrets_basedir)

    def secrets_basedir_create(self, mode=DEFAULT_MODE):
        """Create secrets root directory"""
        os.makedirs(self.secrets_basedir(),
                    exist_ok=True,
                    mode=mode)

    def environment_path(self, env=None, subdir=None, host=None):
        """Returns the absolute path to secrets environment directory
        or subdirectories within it"""
        if env is None:
            env = self._environment
        _path = os.path.join(self.secrets_basedir(), env)

        if not (subdir is None and host is None):
            valid_subdir = r'a-zA-Z0-9_/'
            invalid_subdir = re.compile('[^{}]'.format(valid_subdir))
            valid_host = r'a-zA-Z0-9_\./'  # noqa
            invalid_host = re.compile('[^{}]'.format(valid_host))

            if subdir is None and host is not None:
                raise RuntimeError(
                    '[-] Must specify subdir when specifying host')

            if subdir is not None:
                if subdir.startswith('/'):
                    raise RuntimeError('[-] subdir may not start with "/"')
                elif subdir.endswith('/'):
                    raise RuntimeError('[-] subdir may not end with "/"')
                if not bool(invalid_subdir.search(subdir)):
                    _path = os.path.join(_path, subdir)
                else:
                    raise RuntimeError("[-] invalid character in subdir: "
                                       f"must be in [{valid_subdir}]")

            if host is not None:
                if not bool(invalid_host.search(host)):
                    _path = os.path.join(_path, host)
                else:
                    raise RuntimeError(
                        "[-] invalid character in host: "
                        f"must be in [{valid_host}]")

        return _path

    def environment_exists(self, env=None, path_only=False):
        """Return whether secrets environment directory exists
        and contains files"""
        _ep = self.environment_path(env=env)
        result = os.path.isdir(self.descriptions_path())
        if not result and os.path.exists(_ep):
            if path_only:
                result = True
            else:
                _files = list()
                for root, directories, filenames in os.walk(_ep):
                    for filename in filenames:
                        _files.append(os.path.join(root, filename))
                result = len(_files) > 0
        return result

    def environment_create(self,
                           source=None,
                           alias=False,
                           mode=DEFAULT_MODE):
        """Create secrets environment directory"""
        env_path = self.environment_path()
        if not alias:
            # Create a new environment (optionally from an
            # existing environment)
            if self.environment_exists():
                raise RuntimeError(
                    f"[-] environment '{self._environment}' "
                    "already exists")
            os.makedirs(env_path,
                        exist_ok=True,
                        mode=mode)
            if source is not None:
                self.clone_from(source)
        else:
            # Just create an alias (symbolic link) to
            # an existing environment
            if self.environment_exists():
                raise RuntimeError(
                    f"[-] environment '{self._environment}' "
                    "already exists")
            source_env = SecretsEnvironment(environment=source)
            # Create a symlink with a relative path
            os.symlink(source_env.environment(), env_path)

    def secrets_file_path(self, env=None):
        """Returns the absolute path to secrets file"""
        if env is None:
            env = self._environment
        return os.path.join(self.secrets_basedir(),
                            env,
                            self._secrets_file)

    def secrets_file_path_exists(self):
        """Return whether secrets file exists"""
        return os.path.exists(self.secrets_file_path())

    def descriptions_path(
        self,
        root=None,
        group=None,
        create=False,
        mode=DEFAULT_MODE
    ):
        """Return path to secrets descriptions directory or file."""
        if root is not None:
            path = os.path.join(os.path.abspath(root),
                                self._secrets_descriptions)
        else:
            path = os.path.join(self.environment_path(),
                                self._secrets_descriptions)
        if create:
            os.makedirs(path,
                        exist_ok=True,
                        mode=mode)
        if group is not None:
            path = os.path.join(path, f"{group}.json")
        return path

    def tmpdir_path(self):
        """Return the absolute path to secrets descriptions tmp directory"""
        return os.path.join(self.environment_path(), "tmp")

    def requires_environment(self, path_only=False):
        """
        Provide consistent error handling for any commands that require
        an environment actually exist in order to work properly.
        """
        if not self.environment_exists(path_only=path_only):
            raise RuntimeError(
                f"[-] environment '{self._environment}' "
                "does not exist or is empty")

    def keys(self):
        """Return the keys to the secrets dictionary"""
        return [s for s in self._secrets.keys()]

    def items(self):
        """Return the items from the secrets dictionary."""
        return self._secrets.items()

    def get_secret(self, secret, allow_none=False):
        """Get the value of secret

        :param secret: :type: string
        :return: value of secret
        """
        if secret is None:
            raise RuntimeError('[-] must specify secret to get')
        v = self._secrets.get(secret, None)
        if v is None and not allow_none:
            raise RuntimeError(f"[-] '{secret}' is not defined")
        return v

    def get_secret_export(self, secret):
        """Get the specified environment variable for exporting secret

        :param secret: :type: string
        :return: environment variable for exporting secret
        """
        return self.Export.get(secret, secret)

    def _set_secret(self, secret, value):
        """Set secret to value and export environment variable

        :param secret: :type: string
        :param value: :type: string
        :return:
        """
        self._secrets[secret] = value  # DEPRECATED
        getattr(self, 'Variable')[secret] = value
        if self.export_env_vars:
            if self.preserve_existing and bool(os.getenv(secret)):
                raise RuntimeError(
                    "[-] refusing to overwrite environment "
                    f"variable '{secret}'")
            # Export with secrets name first.
            os.environ[secret] = str(value)
            # See if an alternate environment variable name is
            # defined and also export as that.
            # TODO(dittrich): Support more than one, someday, maybe?
            _env_var = self.get_secret_export(secret)
            if _env_var is None:
                if self.env_var_prefix is not None:
                    _env_var = '{}{}'.format(self.env_var_prefix, secret)
                else:
                    _env_var = secret
            if self.preserve_existing and bool(os.getenv(_env_var)):
                raise RuntimeError(
                    "[-] refusing to overwrite environment "
                    f"variable '{_env_var}'")
            os.environ[_env_var] = str(value)

    def set_secret(self, secret, value=None):
        """Set secret to value and record change

        :param secret: :type: string
        :param value: :type: string
        :return:
        """
        self._set_secret(secret, value)  # DEPRECATED
        getattr(self, 'Variable', {secret: value})
        self._changed = True

    def delete_secret(self, secret):
        """Delete a secret and record change.

        :param secret: :type: string
        :return:
        """
        try:
            del(self.Variable[secret])
        except KeyError:
            pass
        else:
            self._changed = True

    def get_type(self, variable):
        """Return type for variable or None if no description"""
        return self.Type.get(variable, None)

    def read_secrets_and_descriptions(self):
        """Read secrets descriptions and secrets."""
        self.read_secrets_descriptions()
        self.read_secrets(from_descriptions=True)
        self.find_new_secrets()

    def find_new_secrets(self):
        """
        Ensure that any new secrets defined in description files are
        called out and/or become new undefined secrets.
        :return:
        """
        # TODO(dittrich): Replace this with simpler use of attribute maps
        for group in self._descriptions.keys():
            for i in self._descriptions[group]:
                if not len(i):
                    raise RuntimeError(
                        f"[-] found empty dictionary item in group '{group}'")
                s = i['Variable']
                t = i['Type']
                if self.get_secret(s, allow_none=True) is None:
                    if self.verbose_level > 1:
                        self.LOG.warning(
                            f"[!] new {t} variable '{s}' "
                            "is not defined")
                    self._set_secret(s, None)

    def read_secrets(self, from_descriptions=False):
        """
        Load the current secrets file.

        If no secrets have been set yet and from_descriptions is True,
        return a dictionary comprised of the keys from the
        descriptions dictionary defined to be None and set self._changed
        to ensure these are written out.
        """
        _fname = self.secrets_file_path()
        yaml_fname = f"{os.path.splitext(_fname)[0]}.yml"
        # TODO(dittrich): Add upgrade feature... some day.
        # Until then, reference a way for anyone affected to manually
        # convert files.
        if os.path.exists(yaml_fname):
            raise RuntimeError(
                f"[-] old YAML style file '{yaml_fname}' found:\n"
                f"[-] see ``psec utils yaml-to-json --help`` for "
                "information about converting to JSON")
        self.LOG.debug(f"[+] reading secrets from '{_fname}'")
        try:
            with open(_fname, 'r') as f:
                _secrets = json.load(f, object_pairs_hook=OrderedDict)
            for k, v in _secrets.items():
                self._set_secret(k, v)
        except FileNotFoundError as err:
            if from_descriptions:
                for group in self._descriptions.keys():
                    for i in self._descriptions[group]:
                        self._set_secret(i['Variable'], None)
                # Ensure these get written out to create a secrets file.
                self._changed = True
            else:
                raise err
        return self

    def write_secrets(self):
        """Write out the current secrets if any changes were made"""
        if self._changed:
            _fname = self.secrets_file_path()
            self.LOG.debug(f"[+] writing secrets to '{_fname}'")
            with open(_fname, 'w') as f:
                json.dump(self.Variable, f, indent=2)
                f.write('\n')
            self._changed = False
            psec.utils.remove_other_perms(_fname)
        else:
            self.LOG.debug('[-] not writing secrets (unchanged)')

    def clone_from(self, src=None):
        """
        Clone from existing definition file(s)

        The source can be (a) a directory full of one or more
        group descriptions, (b) a single group descriptions file,
        or (c) an existing environment's descriptions file(s).
        """
        src = src.strip('/')
        if src in ['', None]:
            raise RuntimeError('[-] no source provided')
        if os.path.isdir(src):
            if not src.endswith('.d'):
                raise RuntimeError(
                    "[-] refusing to process a directory without "
                    f"a '.d' extension ('{src}')")
        elif os.path.isfile(src) and not src.endswith('.json'):
            raise RuntimeError(
                "[-] refusing to process a file without "
                f"a '.json' extension ('{src}')")
        if not (os.path.exists(src) or self.environment_exists(env=src)):
            raise RuntimeError(
                f"[-] '{src}' does not exist")
        dest = self.descriptions_path(create=True)
        if src.endswith('.d'):
            # Copy anything when cloning from directory.
            src_files = get_files_from_path(src)
            for src_file in src_files:
                copy(src_file, dest)
        elif src.endswith('.json'):
            # Copy just the one file when cloning from a file.
            copy(src, dest)
        else:
            # Only copy descriptions when cloning from environment.
            src_env = SecretsEnvironment(environment=src)
            copydescriptions(
                src_env.descriptions_path(),
                dest
            )
        psec.utils.remove_other_perms(dest)
        self.read_secrets_descriptions()
        self.find_new_secrets()

    def read_descriptions(self, infile=None, group=None):
        """
        Read a secrets group description file and return a dictionary if valid.

        :param infile:
        :param group:
        :return: dictionary of descriptions
        """
        if group is not None:
            # raise RuntimeError('[!] no group specified')
            infile = self.descriptions_path(group=group)
        if infile is None:
            raise RuntimeError(
                '[!] must specify an existing group or file to read')
        with open(infile, 'r') as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
        for d in data:
            for k in d.keys():
                if k not in SECRET_ATTRIBUTES:
                    raise RuntimeError(
                        f"[-] invalid attribute '{k}' in '{infile}'")
        return data

    def write_descriptions(
        self,
        data={},
        group=None,
        mode=DEFAULT_MODE,
        mirror_to=None
    ):
        """Write out the secrets descriptions to a file."""
        if group is None:
            raise RuntimeError('[!] no group specified')
        outfiles = [self.descriptions_path(group=group)]
        if mirror_to is not None:
            outfiles.append(self.descriptions_path(root=mirror_to,
                                                   group=group))
        for outfile in outfiles:
            os.makedirs(os.path.dirname(outfile),
                        exist_ok=True,
                        mode=mode)
            with open(outfile, 'w') as f:
                f.write(json.dumps(data, indent=2))
                f.write('\n')

    def check_duplicates(self, data=list()):
        """
        Check to see if any 'Variable' dictionary elements in list match
        any already defined variables. If so, raise RuntimeError().

        :param data: list of dictionaries containing secret descriptions
        :return: None
        """
        for d in data:
            v = d.get('Variable')
            if v in self._secrets:
                raise RuntimeError(
                    f"[-] variable '{v}' duplicates an existing variable")

    def read_secrets_descriptions(self):
        """Load the descriptions of groups of secrets from a .d directory"""
        groups_dir = self.descriptions_path()
        if not os.path.exists(groups_dir):
            self.LOG.info('[-] secrets descriptions directory not found')
        else:
            # Ignore .order file and any other file extensions
            extensions = ['json']
            file_names = [fn for fn in os.listdir(groups_dir)
                          if any(fn.endswith(ext) for ext in extensions)]
            self.LOG.debug(
                f"[+] reading secrets descriptions from '{groups_dir}'")
            # Iterate over files in directory, loading them into
            # dictionaries as dictionary keyed on group name.
            if len(file_names) == 0:
                self.LOG.info('[-] no secrets descriptions files found')
            for fname in file_names:
                group = os.path.splitext(fname)[0]
                if os.path.splitext(group)[1] != "":
                    raise RuntimeError(
                        f"[-] group name cannot include '.': '{group}'")
                descriptions = self.read_descriptions(group=group)
                if descriptions is not None:
                    self._descriptions[group] = descriptions
                    # Dynamically create maps keyed on variable name
                    # for simpler lookups. (See the get_prompt() method
                    # for an example.)
                    # {'Prompt': 'Google OAuth2 username', 'Type': 'string', 'Variable': 'google_oauth_username'}  # noqa
                    for d in descriptions:
                        # TODO(dittrich): https://github.com/davedittrich/python_secrets/projects/1#card-49358317  # noqa
                        self.Group[d['Variable']] = group
                        for k, v in d.items():
                            try:
                                # Add to existing map
                                getattr(self, k)[d['Variable']] = v
                            except AttributeError:
                                raise RuntimeError(
                                    f"[-] '{k}' is not a valid attribute")
                else:
                    raise RuntimeError(
                        f"[-] descriptions for group '{group}' is empty")

    def descriptions(self):
        return self._descriptions

    def get_secret_type(self, variable):
        """Get the Type of variable from set of secrets descriptions"""
        for g in self._descriptions.keys():
            i = psec.utils.find(
                self._descriptions[g],
                'Variable',
                variable
            )
            if i is not None:
                try:
                    return self._descriptions[g][i]['Type']
                except KeyError:
                    return None
        return None

    def get_options(self, secret):
        """Get the options for setting the secret"""
        return self.Options.get(secret, '*')

    def get_prompt(self, secret):
        """Get the prompt for the secret"""
        return self.Prompt.get(secret, secret)

    # TODO(dittrich): Not very DRY (but no time now)
    def get_secret_arguments(self, variable):
        """Get the Arguments of variable from set of secrets descriptions"""
        for g in self._descriptions.keys():
            i = psec.utils.find(
                self._descriptions[g],
                'Variable',
                variable
            )
            if i is not None:
                try:
                    return self._descriptions[g][i]['Arguments']
                except KeyError:
                    return {}
        return {}

    def get_items_from_group(self, group):
        """Get the variables in a secrets description group"""
        try:
            return [i['Variable'] for i in self._descriptions[group]]
        except KeyError:
            return []

    def is_item_in_group(self, item, group):
        """Return true or false based on item being in group"""
        return psec.utils.find(
            self._descriptions[group],
            'Variable',
            item) is not None

    def get_group(self, item):
        """Return the group to which an item belongs."""
        try:
            return self.Group[item]
        except (KeyError, AttributeError):
            return None

    def get_groups(self):
        """Get the secrets description groups"""
        return [g for g in self._descriptions]


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


def is_generable(secret_type=None):
    """Return boolean for generability of this secret type."""
    generability = {i['Type']: i['Generable'] for i in SECRET_TYPES}
    return generability.get(secret_type, False)


def generate_secret(secret_type=None, *arguments, **kwargs):
    """Generate secret for the type of key"""
    _secret_types = [i['Type'] for i in SECRET_TYPES]
    unique = kwargs.get('unique', False)
    case = kwargs.get('case', 'lower')
    acrostic = kwargs.get('acrostic', None)
    numwords = kwargs.get('numwords', WORDS)
    delimiter = kwargs.get('delimiter', DELIMITER)
    min_words_length = kwargs.get('min_words_length', MIN_WORDS_LENGTH)
    max_words_length = kwargs.get('max_words_length', MAX_WORDS_LENGTH)
    min_acrostic_length = kwargs.get('min_acrostic_length',
                                     MIN_ACROSTIC_LENGTH)
    max_acrostic_length = kwargs.get('max_acrostic_length',
                                     MAX_ACROSTIC_LENGTH)
    wordfile = kwargs.get('wordfile', None)

    if secret_type not in _secret_types:
        raise TypeError(
            f"[-] secret type '{secret_type}' is not supported")
    # The generation functions are memoized, so they can't take keyword
    # arguments. They are instead turned into positional arguments.
    if secret_type == "string":  # nosec
        return None
    if secret_type == "boolean":  # nosec
        return None
    if secret_type == 'password':  # nosec
        return generate_password(unique,
                                 acrostic,
                                 numwords,
                                 case,
                                 delimiter,
                                 min_words_length,
                                 max_words_length,
                                 min_acrostic_length,
                                 max_acrostic_length,
                                 wordfile)
    if secret_type == 'crypt_6':  # nosec
        return generate_crypt6(unique)
    elif secret_type == 'token_hex':  # nosec
        return generate_token_hex(unique)
    elif secret_type == 'token_urlsafe':  # nosec
        return generate_token_urlsafe(unique)
    elif secret_type == 'consul_key':  # nosec
        return generate_consul_key(unique)
    elif secret_type == 'zookeeper_digest':  # nosec
        return generate_zookeeper_digest(unique)
    elif secret_type == 'uuid4':  # nosec
        return generate_uuid4(unique)
    elif secret_type == 'random_base64':  # nosec
        return generate_random_base64(unique)
    else:
        raise TypeError("Secret type " +
                        "'{}' is not supported".format(secret_type))


@Memoize
def generate_password(unique,
                      acrostic,
                      numwords,
                      case,
                      delimiter,
                      min_words_length,
                      max_words_length,
                      min_acrostic_length,
                      max_acrostic_length,
                      wordfile):
    """Generate an XKCD style password"""

    # Create a wordlist from the default wordfile.
    if wordfile is None:
        wordfile = xp.locate_wordfile()
    mywords = xp.generate_wordlist(
        wordfile=wordfile,
        min_length=min_words_length,
        max_length=max_words_length)
    if acrostic is None:
        # Chose a random word for acrostic with length
        # equal to desired number of words.
        acrostic = random.choice(  # nosec
            xp.generate_wordlist(
                wordfile=wordfile,
                min_length=numwords,
                max_length=numwords)
        )
    # Create a password with acrostic word
    # See: https://www.unix-ninja.com/p/your_xkcd_passwords_are_pwned
    password = xp.generate_xkcdpassword(mywords,
                                        numwords=numwords,
                                        acrostic=acrostic,
                                        case=case,
                                        delimiter=delimiter)
    return password


@Memoize
def generate_crypt6(unique=False, password=None, salt=None):
    """Generate a crypt() style SHA512 ("$6$") digest"""
    try:  # Python 3
        import crypt
    except ModuleNotFoundError as e:  # noqa
        raise
    if password is None:
        raise RuntimeError('generate_crypt6(): "password" is not defined')
    if salt is None:
        salt = crypt.mksalt(crypt.METHOD_SHA512)
    pword = crypt.crypt(password, salt)
    return pword


@Memoize
def generate_token_hex(unique=False, nbytes=16):
    """Generate an random hexadecimal token."""
    return secrets.token_hex(nbytes=nbytes)


@Memoize
def generate_token_urlsafe(unique=False, nbytes=16):
    """Generate an URL-safe random token."""
    return secrets.token_urlsafe(nbytes=nbytes)


@Memoize
def generate_consul_key(unique=False):
    """
    Generate a consul key.

    Key generated per the following description:
    https://github.com/hashicorp/consul/blob/b3292d13fb8bbc8b14b2a1e2bbae29c6e105b8f4/command/keygen/keygen.go
    """  # noqa
    keybytes = np_random_bytes(16)
    ckey = binascii.b2a_base64(keybytes)
    return ckey.decode("utf-8").strip()


@Memoize
def generate_zookeeper_digest(unique=False, user=None, credential=None):
    """Generate a zookeeper-compatible digest from username and password"""
    if user is None:
        raise RuntimeError('zk_digest(): user is not defined')
    if credential is None:
        raise RuntimeError('zk_digest(): credential is not defined')
    return base64.b64encode(
        hashlib.sha1(user + ":" + credential).digest()  # nosec
                            ).strip()


@Memoize
def generate_digest_sha1(unique=False, user=None, credential=None):
    """Generate a SHA256 digest from username and password"""
    if user is None:
        raise RuntimeError('generate_digest_sha1(): user is not defined')
    if credential is None:
        raise RuntimeError('generate_digest_sha1(): credential is not defined')
    return base64.b64encode(
        hashlib.sha256(user + ":" + credential).digest()
                            ).strip()


@Memoize
def generate_uuid4(unique=False):
    """Generate a UUID4 string"""
    return str(uuid.uuid4())


@Memoize
def generate_random_base64(unique=False, size=DEFAULT_SIZE):
    """Generate random base64 encoded string of 'size' bytes"""
    return base64.b64encode(os.urandom(size)).decode('UTF-8')


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
