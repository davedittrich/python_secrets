# -*- coding: utf-8 -*-

"""
Secrets environment class and related variables, functions.
"""

import base64
import binascii
import hashlib
import json
import logging
import os
import re
#
# WARNING: When commands in a cliff app are implemented as Python modules,
# there is a risk of shadowing Python internal modules. In this case,
# the command group 'secrets' may cause import conflicts with the Python
# 'secrets' module. Keep that in mind when making changes. It is imported
# directly here (rather than using 'from ... import') to avoid the conflict.
import secrets
#
import uuid

from collections import OrderedDict
from pathlib import Path
from shutil import copy
from stat import S_IMODE
from xkcdpass import xkcd_password as xp

from psec.exceptions import (
    BasedirNotFoundError,
    SecretNotFoundError,
)
from psec.utils import (
    copydescriptions,
    find,
    get_default_environment,
    get_default_secrets_basedir,
    get_files_from_path,
    is_secrets_basedir,
    remove_other_perms,
    secrets_basedir_create,
    DEFAULT_MODE,
    Memoize,
    SECRETS_DESCRIPTIONS_DIR,
    SECRETS_FILE,
)


logger = logging.getLogger(__name__)


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
# TODO(dittrich): Replace this with pydantic classes at some point.
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
            'Description': '32-bit hexadecimal token',
            'Generable': True}),
        OrderedDict({
            'Type': 'token_urlsafe',
            'Description': '32-bit URL-safe token',
            'Generable': True}),
        OrderedDict({
            'Type': 'consul_key',
            'Description': '32-byte BASE64 token',
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
    'Help',
    'Type',
    'Export',
    'Prompt',
    'Options'
]

# XKCD password defaults
# See: https://www.unix-ninja.com/p/your_xkcd_passwords_are_pwned
WORDS = 4
MIN_WORDS_LENGTH = 3
MAX_WORDS_LENGTH = 6
MIN_ACROSTIC_LENGTH = 6
MAX_ACROSTIC_LENGTH = 6
DELIMITER = '.'


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
        return generate_password(
            unique,
            acrostic,
            numwords,
            case,
            delimiter,
            min_words_length,
            max_words_length,
            min_acrostic_length,
            max_acrostic_length,
            wordfile,
        )
    if secret_type == 'crypt_6':  # nosec
        return generate_crypt6(unique)
    if secret_type == 'token_hex':  # nosec
        return generate_token_hex(unique)
    if secret_type == 'token_urlsafe':  # nosec
        return generate_token_urlsafe(unique)
    if secret_type == 'consul_key':  # nosec
        return generate_consul_key(unique)
    if secret_type == 'zookeeper_digest':  # nosec
        return generate_zookeeper_digest(unique)
    if secret_type == 'uuid4':  # nosec
        return generate_uuid4(unique)
    if secret_type == 'random_base64':  # nosec
        return generate_random_base64(unique)
    raise TypeError(f"Secret type '{secret_type}' is not supported")


@Memoize
def generate_password(
    unique,
    acrostic,
    numwords,
    case,
    delimiter,
    min_words_length,
    max_words_length,
    min_acrostic_length,
    max_acrostic_length,
    wordfile,
):
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
        acrostic = secrets.choice(
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
        import crypt  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError as e:  # noqa
        raise
    if password is None:
        raise RuntimeError('generate_crypt6(): "password" is not defined')
    if salt is None:
        salt = crypt.mksalt(crypt.METHOD_SHA512)
    pword = crypt.crypt(password, salt)
    return pword


@Memoize
def generate_token_hex(unique=False, nbytes=32):
    """Generate an random hexadecimal token."""
    return secrets.token_hex(nbytes=nbytes)


@Memoize
def generate_token_urlsafe(unique=False, nbytes=32):
    """Generate an URL-safe random token."""
    return secrets.token_urlsafe(nbytes=nbytes)


@Memoize
def generate_consul_key(unique=False):
    """
    Generate a consul key.
    https://www.consul.io/docs/security/encryption

    Key generated per the following description:
    https://github.com/hashicorp/consul/blob/b3292d13fb8bbc8b14b2a1e2bbae29c6e105b8f4/command/keygen/keygen.go
    """  # noqa
    keybytes = secrets.token_bytes(32)
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


class SecretsEnvironment(object):
    """
    Class for handling secrets environment metadata.

    Provides an interface to the directory contents for a secrets environment,
    including groups descriptions, a tmp/ directory, and any other required
    directories.

      Typical usage example::

          from psec.secrets_environment import SecretsEnvironment

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

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        environment=None,
        secrets_basedir=None,
        secrets_file=None,
        create_root=False,
        defer_loading=False,
        export_env_vars=False,
        preserve_existing=False,
        env_var_prefix=None,
        source=None,
        verbose_level=1,
    ):
        """
        Initialize secrets environment object.
        """
        if secrets_file and secrets_basedir:
            raise RuntimeError(
                "[-] 'secrets_file' and 'secrets_basedir' are mutually "
                "exclusive when initializing a SecretsEnvironment()"
            )
        self._environment = (
            get_default_environment() if environment is None
            else environment
        )
        if secrets_basedir is None:
            secrets_basedir = get_default_secrets_basedir()
        try:
            is_secrets_basedir(basedir=secrets_basedir, raise_exception=True)
            self._secrets_basedir = Path(secrets_basedir)
        except BasedirNotFoundError:
            if create_root:
                self._secrets_basedir = secrets_basedir_create(
                    basedir=secrets_basedir
                )
            else:
                raise
        if secrets_file is not None:
            self._secrets_file = Path(secrets_file)
            if len(self._secrets_file.parts) < 3:
                # This might not exactly be true in all cases, but I don't
                # have time to run down all possible use cases (or put in
                # all necessary checks) at the moment.
                raise RuntimeError(
                    '[-] the path to a secrets file should have '
                    f"at least 3 components ('{self._secrets_file}')"
                )
            if not self._secrets_file.exists():
                raise RuntimeError(
                    f"[-] the specified secrets file '{secrets_file}' "
                    'does not exist'
                )
            if self._environment != self._secrets_file.parts[-2]:
                raise RuntimeError(
                    f"[-] environment name '{environment}' does not "
                    f"match secrets file path '{secrets_file}'"
                )
            if Path(secrets_basedir) not in self._secrets_file.parents:
                raise RuntimeError(
                    f"[-] base directory '{secrets_basedir}' does not "
                    f"match secrets file path '{secrets_file}'"
                )
            self.secrets_basedir = self._secrets_file.parents[1]
        else:
            self._secrets_file = self._secrets_basedir / self._environment / SECRETS_FILE  # noqa
        self._secrets_descriptions = self._secrets_file.parent / SECRETS_DESCRIPTIONS_DIR # noqa
        self._verbose_level = verbose_level
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
            os.environ['D2_ENVIRONMENT'] = self._environment
            # Deprecating this variable name:
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
        self._changed = False

    def __str__(self):
        """Produce string representation of environment identifier"""
        return str(self._environment)

    @property
    def verbose_level(self):
        """Returns the verbosity level."""
        return self._verbose_level

    def changed(self):
        """Return boolean reflecting changed secrets."""
        return self._changed

    # TODO(dittrich): FIX Cere call
    def get_secrets_descriptions_dir(self):
        """Return the path to the drop-in secrets description directory"""
        _env = self._environment
        if not _env:
            return self.get_secrets_basedir()
        else:
            return self.get_secrets_basedir() / self.get_secrets_basename().replace('.json', '.d')  # noqa

    def get_secrets_basename(self):
        """Return the basename of the current secrets file"""
        return os.path.basename(self._secrets_file)

    def get_secrets_basedir(self, init=False, mode=DEFAULT_MODE):
        """
        Returns the directory path root for secrets storage and definitions.

        When more than one environment is being used, a single top-level
        directory in the user's home directory is the preferred location.
        This function checks to see if such a directory exists, and if
        so defaults to that location.

        If the environment variable "D2_SECRETS_BASEDIR" is set, that location
        is used instead.
        """
        try:
            secrets_basedir = self._secrets_basedir
        except AttributeError:
            secrets_basedir = get_default_secrets_basedir()
        if init:
            secrets_basedir_create(
                basedir=secrets_basedir,
                mode=mode,
            )
        else:
            is_secrets_basedir(basedir=secrets_basedir, raise_exception=True)
        return secrets_basedir

    def secrets_basedir_exists(self):
        """Return whether secrets root directory exists"""
        return self._secrets_basedir.exists()

    def get_environment_path(self, env=None, subdir=None, host=None):
        """Returns the absolute path to secrets environment directory
        or subdirectories within it"""
        if env is None:
            env = self._environment
        _path = self.get_secrets_basedir() / env
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
                    _path = _path / subdir
                else:
                    raise RuntimeError(
                        "[-] invalid character in subdir: "
                        f"must be in [{valid_subdir}]"
                    )
            if host is not None:
                if not bool(invalid_host.search(host)):
                    _path = _path / host
                else:
                    raise RuntimeError(
                        "[-] invalid character in host: "
                        f"must be in [{valid_host}]")
        return Path(_path)

    def environment_exists(self, env=None, path_only=False):
        """Return whether secrets environment directory exists
        and contains files other than 'tmp' directory."""
        _ep = self.get_environment_path(env=env)
        result = os.path.isdir(self.get_descriptions_path())
        if not result and os.path.exists(_ep):
            if path_only:
                result = True
            else:
                _files = list()
                for root, _, filenames in os.walk(_ep):
                    for filename in filenames:
                        if filename != 'tmp':
                            _files.append(os.path.join(root, filename))
                result = len(_files) > 0
        return result

    def environment_create(self,
                           source=None,
                           alias=False,
                           mode=DEFAULT_MODE):
        """Create secrets environment directory"""
        env_path = self.get_environment_path()
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
            os.symlink(str(source_env), env_path)

    def get_secrets_file_path(self, env=None):
        """Returns the absolute path to secrets file"""
        if env is None:
            env = self._environment
        return self.get_secrets_basedir() / env / self._secrets_file

    def secrets_file_path_exists(self):
        """Return whether secrets file exists"""
        return os.path.exists(self.get_secrets_file_path())

    def get_descriptions_path(
        self,
        root=None,
        group=None,
        create=False,
        mode=DEFAULT_MODE
    ):
        """Return path to secrets descriptions directory or file."""
        if root is not None:
            path = Path(root) / self._secrets_descriptions
        else:
            path = self.get_environment_path() / self._secrets_descriptions
        if create:
            path.mkdir(parents=True, exist_ok=True, mode=mode)
        if group is not None:
            path = path / f"{group}.json"
        return path

    def get_tmpdir_path(self, create_path=False):
        """Return the absolute path to secrets descriptions tmp directory"""
        tmpdir = self.get_environment_path() / "tmp"
        if create_path:
            tmpdir_mode = 0o700
            try:
                os.makedirs(tmpdir, tmpdir_mode)
                self.logger.info("[+] created tmpdir %s", tmpdir)
            except FileExistsError:
                mode = os.stat(tmpdir).st_mode
                current_mode = S_IMODE(mode)
                if current_mode != tmpdir_mode:
                    os.chmod(tmpdir, tmpdir_mode)
                    self.logger.info(
                        "[+] changed mode on %s from %s to %s",
                        oct(current_mode),
                        oct(tmpdir_mode),
                        tmpdir
                    )
        return tmpdir

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

        Args:
            secret (string): Name of the secret to get
            allow_none (boolean): Allow returning ``None``

        Returns:
            string: The value of the secret

        Raises:
            SecretNotFoundError: If value is ``None`` and
                ``allow_none`` is ``False``

        """
        if secret is None:
            raise RuntimeError('[-] must specify secret to get')
        v = self._secrets.get(secret, None)
        if v is None and not allow_none:
            raise SecretNotFoundError(f"[-] '{secret}' is not defined")
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
            del self.Variable[secret]
        except KeyError:
            pass
        else:
            self._changed = True

    def get_type(self, variable):
        """Return type for variable or None if no description"""
        return self.Type.get(variable, None)

    def get_default_value(self, variable):
        """Return the default value from the Options attribute"""
        try:
            values = self.Options.get(variable).split(',')
        except AttributeError:
            values = []
        return (
            values[0]
            if len(values) > 0 and values[0] != '*'
            else ''
        )

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
                if len(i) == 0:
                    raise RuntimeError(
                        f"[-] found empty dictionary item in group '{group}'")
                s = i['Variable']
                t = i['Type']
                if self.get_secret(s, allow_none=True) is None:
                    if self.verbose_level > 1:
                        self.logger.warning(
                            "[!] new %s variable '%s' is not defined",
                            t,
                            s
                        )
                    self._set_secret(s, None)

    def read_secrets(self, from_descriptions=False):
        """
        Load the current secrets file.

        If no secrets have been set yet and from_descriptions is True,
        return a dictionary comprised of the keys from the
        descriptions dictionary defined to be None and set self._changed
        to ensure these are written out.
        """
        _fname = self.get_secrets_file_path()
        yaml_fname = f"{os.path.splitext(_fname)[0]}.yml"
        # TODO(dittrich): Add upgrade feature... some day.
        # Until then, reference a way for anyone affected to manually
        # convert files.
        if os.path.exists(yaml_fname):
            raise RuntimeError(
                f"[-] old YAML style file '{yaml_fname}' found:\n"
                f"[-] see ``psec utils yaml-to-json --help`` for "
                "information about converting to JSON")
        self.logger.debug("[+] reading secrets from '%s'", _fname)
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
            _fname = self.get_secrets_file_path()
            self.logger.debug("[+] writing secrets to '%s'", _fname)
            with open(_fname, 'w') as f:
                json.dump(self.Variable, f, indent=2)
                f.write('\n')
            self._changed = False
            remove_other_perms(_fname)
        else:
            self.logger.debug('[-] not writing secrets (unchanged)')

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
                f"[-] directory or environment '{src}' does not exist")
        dest = self.get_descriptions_path(create=True)
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
                src_env.get_descriptions_path(),
                dest
            )
        remove_other_perms(dest)
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
            infile = self.get_descriptions_path(group=group)
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
        outfiles = [self.get_descriptions_path(group=group)]
        if mirror_to is not None:
            outfiles.append(
                self.get_descriptions_path(
                    root=mirror_to,
                    group=group,
                )
            )
        for outfile in outfiles:
            os.makedirs(os.path.dirname(outfile),
                        exist_ok=True,
                        mode=mode)
            with open(outfile, 'w') as f:
                f.write(json.dumps(data, indent=2))
                f.write('\n')

    def check_duplicates(self, data=None):
        """
        Check to see if any 'Variable' dictionary elements in list match
        any already defined variables. If so, raise RuntimeError().

        :param data: list of dictionaries containing secret descriptions
        :return: None
        """
        if isinstance(data, list):
            for d in data:
                v = d.get('Variable')
                if v in self._secrets:
                    raise RuntimeError(
                        f"[-] variable '{v}' duplicates an existing variable"
                    )

    def read_secrets_descriptions(self):
        """Load the descriptions of groups of secrets from a .d directory"""
        groups_dir = self.get_descriptions_path()
        if not os.path.exists(groups_dir):
            self.logger.info('[-] secrets descriptions directory not found')
        else:
            # Ignore .order file and any other file extensions
            extensions = ['json']
            file_names = [fn for fn in os.listdir(groups_dir)
                          if any(fn.endswith(ext) for ext in extensions)]
            self.logger.debug(
                "[+] reading secrets descriptions from '%s'", groups_dir)
            # Iterate over files in directory, loading them into
            # dictionaries as dictionary keyed on group name.
            if len(file_names) == 0:
                self.logger.info('[-] no secrets descriptions files found')
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
            i = find(
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

    def get_help(self, secret):
        """Get the help documentation URL for the secret"""
        return self.Help.get(secret, '*')

    def get_prompt(self, secret):
        """Get the prompt for the secret"""
        return self.Prompt.get(secret, secret)

    # TODO(dittrich): Not very DRY (but no time now)
    def get_secret_arguments(self, variable):
        """Get the Arguments of variable from set of secrets descriptions"""
        for g in self._descriptions.keys():
            i = find(
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
        return find(
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


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
