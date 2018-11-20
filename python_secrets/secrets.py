import base64
import binascii
import errno
import hashlib
import logging
import os
import random
import re
import secrets
import textwrap
import uuid
import yaml

from cliff.command import Command
from cliff.lister import Lister
from numpy.random import bytes as np_random_bytes
from python_secrets.utils import redact, find, prompt_string
from python_secrets.google_oauth2 import GoogleSMTP
from shutil import copy, copytree
# >> Issue: [B404:blacklist] Consider possible security implications associated with run module.  # noqa
#    Severity: Low   Confidence: High
#    Location: python_secrets/secrets.py:21
#    More Info: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess  # noqa
from subprocess import run, PIPE  # nosec
from xkcdpass import xkcd_password as xp

DEFAULT_SIZE = 18
SECRET_TYPES = [
        {'Type': 'password', 'Description': 'Simple (xkcd) password string'},
        {'Type': 'string', 'Description': 'Simple string'},
        {'Type': 'crypt_6', 'Description': 'crypt() SHA512 ("$6$")'},
        {'Type': 'token_hex', 'Description': 'Hexadecimal token'},
        {'Type': 'token_urlsafe', 'Description': 'URL-safe token'},
        {'Type': 'consul_key', 'Description': '16-byte BASE64 token'},
        {'Type': 'sha1_digest', 'Description': 'DIGEST-SHA1 (user:pass) digest'},  # noqa
        {'Type': 'sha256_digest', 'Description': 'DIGEST-SHA256 (user:pass) digest'},  # noqa
        {'Type': 'zookeeper_digest', 'Description': 'DIGEST-SHA1 (user:pass) digest'},  # noqa
        {'Type': 'uuid4', 'Description': 'UUID4 token'},
        {'Type': 'random_base64', 'Description': 'Random BASE64 token'}
        ]
SECRET_ATTRIBUTES = [
    'Variable',
    'Type',
    'Export',
    'Prompt'
]
DEFAULT_MODE = 0o710


def copyanything(src, dst):
    try:
        copytree(src, dst)
    except FileExistsError as e:  # noqa
        pass
    except OSError as exc:  # python >2.5
        if exc.errno == errno.ENOTDIR:
            copy(src, dst)
        else:
            raise


def _identify_environment(environment=None):
    """
    Returns the environment identifier.

    There are multiple ways to define the default environment (in order
    of priority):

    1. The --environment command line option;
    2. The content of the file .python_secrets_environment in the current
       working directory;
    3. The value specified by environment variable D2_ENVIRONMENT; or
    4. The basename of the current working directory.
    """
    cwd = os.getcwd()
    if environment is None:
        env_file = os.path.join(cwd, '.python_secrets_environment')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                environment = f.read().replace('\n', '')
        else:
            environment = os.getenv('D2_ENVIRONMENT',
                                    os.path.basename(cwd))
    return environment


class SecretsEnvironment(object):
    """Class for handling secrets environment metadata"""

    LOG = logging.getLogger(__name__)

    def __init__(self,
                 environment=None,
                 secrets_basedir=None,
                 secrets_file=os.getenv('D2_SECRETS_BASENAME',
                                        'secrets.yml'),
                 create_root=True,
                 defer_loading=True,
                 export_env_vars=False,
                 env_var_prefix=None,
                 source=None,
                 cwd=os.getcwd()):
        self._cwd = cwd
        self._environment = _identify_environment(environment)
        self._secrets_file = secrets_file
        self._secrets_basedir = secrets_basedir
        # Ensure root directory exists in which to create secrets
        # environments?
        if not self.secrets_basedir_exists():
            if create_root:
                self.secrets_basedir_create()
            else:
                raise RuntimeError(
                    'Directory {} '.format(self.secrets_basedir()) +
                    'does not exist and create_root=False')
        self._secrets_descriptions = "{}.d".format(
            os.path.splitext(self._secrets_file)[0])
        self.export_env_vars = export_env_vars

        # When exporting environment variables, include one that specifies the
        # environment from which these variables were derived. This also works
        # around a limitation in Ansible where the current working directory
        # from which "ansible" was run. (The D2 lookup_plugin/python_secrets.py
        # script needs to communicate this back to python_secrets in order for
        # it's .python_secrets_environment file to be used to identify the
        # proper environment.)

        if self.export_env_vars is True:
            os.environ['PYTHON_SECRETS_ENVIRONMENT'] = self.environment()

        self.env_var_prefix = env_var_prefix
        # Secrets attribute maps; anything else throws exception
        for a in SECRET_ATTRIBUTES:
            setattr(self, a, dict())
        if source is not None:
            self.clone_from(source)
            self.read_secrets_descriptions()
        self._secrets = dict()
        self._descriptions = dict()
        self._changed = False
        self._groups = []

    def environment(self):
        """Returns the environment identifier."""
        return self._environment

    # TODO(dittrich): FIX Cere call
    def secrets_descriptions_dir(self):
        """Return the path to the drop-in secrets description directory"""
        _env = self.environment()
        if not _env:
            return self.secrets_basedir()
        else:
            return os.path.join(self.secrets_basedir(),
                                self.secrets_basename().replace('.yml', '.d'))

    def secrets_basename(self):
        """Return the basename of the current secrets file"""
        return os.path.basename(self._secrets_file)

    # def secrets_basedir(self):
    #     """Return the basedir of the current secrets file"""
    #     return os.path.dirname(self._secrets_file)

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
        os.mkdir(self.secrets_basedir(), mode=mode)

    def environment_path(self, subdir=None, host=None):
        """Returns the absolute path to secrets environment directory
        or subdirectories within it"""
        _path = os.path.join(self.secrets_basedir(), self.environment())

        if not (subdir is None and host is None):
            valid_subdir = 'a-zA-Z0-9_/'
            invalid_subdir = re.compile('[^{}]'.format(valid_subdir))
            valid_host = 'a-zA-Z0-9_\./'  # noqa
            invalid_host = re.compile('[^{}]'.format(valid_host))

            if subdir is None and host is not None:
                raise RuntimeError('Must specify subdir when specifying host')

            if subdir is not None:
                if subdir.startswith('/'):
                    raise RuntimeError('subdir may not start with "/"')
                elif subdir.endswith('/'):
                    raise RuntimeError('subdir may not end with "/"')
                if not bool(invalid_subdir.search(subdir)):
                    _path = os.path.join(_path, subdir)
                else:
                    raise RuntimeError('Invalid character in subdir: ' +
                                       'must be in [{}]'.format(valid_subdir))

            if host is not None:
                if not bool(invalid_host.search(host)):
                    _path = os.path.join(_path, host)
                else:
                    raise RuntimeError('Invalid character in host: ' +
                                       'must be in [{}]'.format(valid_host))

        return _path

    def environment_exists(self):
        """Return whether secrets environment directory exists
        and contains files"""
        _ep = self.environment_path()
        _files = list()
        for root, directories, filenames in os.walk(_ep):
            for filename in filenames:
                _files.append(os.path.join(root, filename))
        return os.path.exists(_ep) and len(_files) > 0

    def environment_create(self,
                           source=None,
                           mode=DEFAULT_MODE):
        """Create secrets environment directory"""
        _path = self.environment_path()
        if not os.path.exists(_path):
            if source is not None:
                self.clone_from(source)
            else:
                os.mkdir(_path, mode=mode)
                self.descriptions_path_create()
        else:
            if self.environment_exists():
                raise RuntimeError('Environment "{}" exists'.format(
                    self.environment()))

    def secrets_file_path(self):
        """Returns the absolute path to secrets file"""
        if self.environment() is None:
            return os.path.join(self.secrets_basedir(), self._secrets_file)
        else:
            return os.path.join(self.secrets_basedir(),
                                self.environment(),
                                self._secrets_file)

    def secrets_file_path_exists(self):
        """Return whether secrets file exists"""
        return os.path.exists(self.secrets_file_path())

    def descriptions_path(self):
        """Return the absolute path to secrets descriptions directory"""
        return os.path.join(self.environment_path(),
                            self._secrets_descriptions)

    def descriptions_path_exists(self):
        """Return whether secrets descriptions directory exists"""
        return os.path.exists(self.descriptions_path())

    def descriptions_path_create(self, mode=DEFAULT_MODE):
        """Create secrets descriptions directory"""
        if not self.environment_exists():
            self.environment_create(mode=mode)
        if not self.descriptions_path_exists():
            os.mkdir(self.descriptions_path(), mode=mode)

    def tmpdir_path(self):
        """Return the absolute path to secrets descriptions tmp directory"""
        return os.path.join(self.environment_path(), "tmp")

    def requires_environment(self):
        """
        Provide consistent error handling for any commands that require
        an environment actually exist in order to work properly.
        """
        if not self.environment_exists():
            raise RuntimeError(
                'environment "{}" does not exist'.format(self.environment()))

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
            raise RuntimeError('Must specify secret to get')
        v = self._secrets.get(secret, None)
        if v is None and not allow_none:
            raise RuntimeError('{} is not defined'.format(secret))
        return v

    def get_secret_export(self, secret):
        """Get the specified environment variable for exporting secret

        :param secret: :type: string
        :return: environment variable for exporting secret
        """
        return self.Export.get(secret, None)

    def _set_secret(self, secret, value):
        """Set secret to value and export environment variable

        :param secret: :type: string
        :param value: :type: string
        :return:
        """
        self._secrets[secret] = value  # DEPRECATED
        getattr(self, 'Variable')[secret] = value
        if self.export_env_vars:
            _env_var = self.get_secret_export(secret)
            if _env_var is None:
                if self.env_var_prefix is not None:
                    _env_var = '{}{}'.format(self.env_var_prefix, secret)
                else:
                    _env_var = secret
            os.environ[_env_var] = str(value)

    def set_secret(self, secret, value):
        """Set secret to value and record change

        :param secret: :type: string
        :param value: :type: string
        :return:
        """
        self._set_secret(secret, value)  # DEPRECATED
        getattr(self, 'Variable', {secret: value})
        self._changed = True

    def get_type(self, variable):
        """Return type for variable or None if no description"""
        return self.Type.get(variable, None)

    def changed(self):
        """Return boolean reflecting changed secrets."""
        return self._changed

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
                s = i['Variable']
                t = i['Type']
                if self.get_secret(s, allow_none=True) is None:
                    self.LOG.info('new {} '.format(t) +
                                  'variable "{}" '.format(s) +
                                  'is not defined')
                    self._set_secret(s, None)

    def read_secrets(self, from_descriptions=False):
        """
        Load the current secrets from .yml file

        If no secrets have been set yet and from_descriptions is True,
        return a dictionary comprised of the keys from the
        descriptions dictionary defined to be None and set self._changed
        to ensure these are written out.
        """
        _fname = self.secrets_file_path()
        self.LOG.debug('reading secrets from {}'.format(_fname))
        try:
            with open(_fname, 'r') as f:
                _secrets = yaml.safe_load(f)
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

    def write_secrets(self):
        """Write out the current secrets for use by Ansible,
        only if any changes were made"""
        if self._changed:
            _fname = self.secrets_file_path()
            self.LOG.debug('writing secrets to {}'.format(_fname))
            with open(_fname, 'w') as f:
                yaml.dump(self._secrets,
                          f,
                          encoding=('utf-8'),
                          explicit_start=True,
                          default_flow_style=False
                          )
            self._changed = False
        else:
            self.LOG.debug('not writing secrets (unchanged)')

    def clone_from(self, source=None):
        """Clone an existing environment directory (or facsimile there of)"""
        dest = self.environment_path()
        if source is not None:
            copyanything(source, dest)
        self.read_secrets_descriptions()
        self.find_new_secrets()

    def get_descriptions(self, infile=None):
        """
        Read a secrets description file and return a dictionary if valid.

        :param infile:
        :return: dictionary of descriptions
        """
        with open(infile, 'r') as f:
            data = yaml.safe_load(f)
        for d in data:
            for k in d.keys():
                if k not in SECRET_ATTRIBUTES:
                    raise RuntimeError('Invalid attribute ' +
                                       '"{}"'.format(k) +
                                       'in {}'.format(infile))
        return data

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
                raise RuntimeError('Variable "{}" '.format(v) +
                                   'duplicates an existing variable')

    def read_secrets_descriptions(self):
        """Load the descriptions of groups of secrets from a .d directory"""
        groups_dir = self.descriptions_path()
        if not os.path.exists(groups_dir):
            self.LOG.info('secrets descriptions directory not found')
        else:
            # Ignore .order file and any other non-YAML file extensions
            extensions = ['yml', 'yaml']
            file_names = [fn for fn in os.listdir(groups_dir)
                          if any(fn.endswith(ext) for ext in extensions)]
            self._groups = [os.path.splitext(fn) for fn in file_names]
            self.LOG.debug('reading secrets descriptions from {}'.format(
                groups_dir))
            # Iterate over files in directory, loading them into
            # dictionaries as dictionary keyed on group name.
            if len(file_names) == 0:
                self.LOG.info('no secrets descriptions files found')
            for fname in file_names:
                group = os.path.splitext(fname)[0]
                if os.path.splitext(group)[1] != "":
                    raise RuntimeError('Group name cannot include ".": ' +
                                       '{}'.format(group))
                data = self.get_descriptions(
                    os.path.join(groups_dir, fname))
                if data is not None:
                    self._descriptions[group] = data
                    # Dynamically create maps keyed on variable name
                    # for simpler lookups. (See the get_prompt() method
                    # for an example.)
                    for d in data:
                        for k, v in d.items():
                            try:
                                # Add to existing map
                                v = v if v != d['Variable'] else None
                                getattr(self, k)[d['Variable']] = v
                            except AttributeError:
                                raise RuntimeError(
                                    '"{}" is not '.format(k) +
                                    'a valid attribute')
                else:
                    raise RuntimeError('descriptions for group ' +
                                       '"{}" is empty'.format(group))

    def descriptions(self):
        return self._descriptions

    def get_secret_type(self, variable):
        """Get the Type of variable from set of secrets descriptions"""
        for g in self._descriptions.keys():
            i = find(
                self._descriptions[g],
                'Variable',
                variable)
            if i is not None:
                try:
                    return self._descriptions[g][i]['Type']
                except KeyError:
                    return None
        return None

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
                variable)
            if i is not None:
                try:
                    return self._descriptions[g][i]['Arguments']
                except KeyError:
                    return {}
        return {}

    def get_items_from_group(self, group):
        """Get the variables in a secrets description group"""
        return [i['Variable'] for i in self._descriptions[group]]

    def is_item_in_group(self, item, group):
        """Return true or false based on item being in group"""
        return find(
                self._descriptions[group],
                'Variable',
                item) is not None

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


def generate_secret(secret_type=None, unique=False, **kwargs):
    """Generate secret for the type of key"""
    _secret_types = [i['Type'] for i in SECRET_TYPES]
    if secret_type not in _secret_types:
        raise TypeError("Secret type " +
                        "'{}' is not supported".format(secret_type))
    if secret_type == "string":
        return None
    if secret_type == 'password':
        return generate_password(unique)
    if secret_type == 'crypt_6':
        return generate_crypt6(unique, **kwargs)
    elif secret_type == 'token_hex':
        return generate_token_hex(unique, **kwargs)
    elif secret_type == 'token_urlsafe':
        return generate_token_urlsafe(unique, **kwargs)
    elif secret_type == 'consul_key':
        return generate_consul_key(unique)
    elif secret_type == 'zookeeper_digest':
        return generate_zookeeper_digest(unique, **kwargs)
    elif secret_type == 'uuid4':
        return generate_uuid4(unique, **kwargs)
    elif secret_type == 'random_base64':
        return generate_random_base64(unique, **kwargs)
    else:
        raise TypeError("Secret type " +
                        "'{}' is not supported".format(secret_type))


@Memoize
def generate_password(unique=False):
    """Generate an XKCD style password"""
    # create a wordlist from the default wordfile
    # use words between 5 and 8 letters long
    wordfile = xp.locate_wordfile()
    mywords = xp.generate_wordlist(
        wordfile=wordfile,
        min_length=5,
        max_length=8)
    # Chose a random four-letter word for acrostic
    acword = random.choice(  # nosec
        xp.generate_wordlist(
            wordfile=wordfile,
            min_length=4,
            max_length=4)
    )
    # create a password with acrostic word
    pword = xp.generate_xkcdpassword(mywords, acrostic=acword)
    return pword


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
    """Generate a consul key per the following description:
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


class SecretsShow(Lister):
    """List the contents of the secrets file or definitions"""

    LOG = logging.getLogger(__name__)

    # Note: Not totally DRY. Replicates some logic from SecretsDescribe()

    def get_parser(self, prog_name):
        parser = super(SecretsShow, self).get_parser(prog_name)
        # Sorry for the double-negative, but it works better
        # this way for the user as a flag and to have a default
        # of redacting (so they need to turn it off)
        parser.epilog = textwrap.dedent("""

        .. code-block:: console

            $ psec secrets show
            +------------------------+----------+-------------------+----------+  # noqa
            | Variable               | Type     | Export            | Value    |  # noqa
            +------------------------+----------+-------------------+----------+  # noqa
            | jenkins_admin_password | password | None              | REDACTED |  # noqa
            | myapp_app_password     | password | DEMO_app_password | REDACTED |  # noqa
            | myapp_client_psk       | string   | DEMO_client_ssid  | REDACTED |  # noqa
            | myapp_client_ssid      | string   | DEMO_client_ssid  | REDACTED |  # noqa
            | myapp_pi_password      | password | DEMO_pi_password  | REDACTED |  # noqa
            | trident_db_pass        | password | None              | REDACTED |  # noqa
            | trident_sysadmin_pass  | password | None              | REDACTED |  # noqa
            +------------------------+----------+-------------------+----------+  # noqa

        ..
        """)
        redact = not (os.getenv('D2_NO_REDACT', "FALSE").upper()
                      in ["true".upper(), "1", "yes".upper()])
        parser.add_argument(
            '-C', '--no-redact',
            action='store_false',
            dest='redact',
            default=redact,
            help="Do not redact values in output (default: {})".format(redact)
        )
        parser.add_argument(
            '-g', '--group',
            dest='args_group',
            action="store_true",
            default=False,
            help="Arguments are groups to list (default: False)"
        )
        parser.add_argument(
            '-p', '--prompts',
            dest='args_prompts',
            action="store_true",
            default=False,
            help="Include prompts (default: False)"
        )
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('showing secrets')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        variables = []
        if parsed_args.args_group:
            if not len(parsed_args.args):
                raise RuntimeError('No group specified')
            for g in parsed_args.args:
                try:
                    variables.extend(
                        [v for v
                         in self.app.secrets.get_items_from_group(g)]
                    )
                except KeyError as e:
                    raise RuntimeError('Group {} '.format(str(e)) +
                                       'does not exist')
        else:
            variables = parsed_args.args \
                if len(parsed_args.args) > 0 \
                else [k for k, v in self.app.secrets.items()]
        columns = ('Variable', 'Type', 'Export', 'Value')
        data = (
                [(k,
                  self.app.secrets.get_secret_type(k),
                  self.app.secrets.get_secret_export(k),
                  redact(v, parsed_args.redact))
                    for k, v in self.app.secrets.items()
                    if k in variables]
        )
        return columns, data


class SecretsDescribe(Lister):
    """Describe supported secret types"""

    LOG = logging.getLogger(__name__)

    # Note: Not totally DRY. Replicates some logic from SecretsShow()

    def get_parser(self, prog_name):
        parser = super(SecretsDescribe, self).get_parser(prog_name)
        what = parser.add_mutually_exclusive_group(required=False)
        what.add_argument(
            '-g', '--group',
            dest='args_group',
            action="store_true",
            default=False,
            help="Arguments are groups to list (default: False)"
        )
        what.add_argument(
            '-t', '--types',
            dest='types',
            action="store_true",
            default=False,
            help="Describe types (default: False)"
        )
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('describing secrets')
        if parsed_args.types:
            columns = [k.title() for k in SECRET_TYPES[0].keys()]
            data = [[v for k, v in i.items()] for i in SECRET_TYPES]
        else:
            self.app.secrets.requires_environment()
            self.app.secrets.read_secrets_and_descriptions()
            variables = []
            if parsed_args.args_group:
                if not len(parsed_args.args):
                    raise RuntimeError('No group specified')
                for g in parsed_args.args:
                    try:
                        variables.extend(
                            [v for v
                                in self.app.secrets.get_items_from_group(g)]
                        )
                    except KeyError as e:
                        raise RuntimeError('Group {} '.format(str(e)) +
                                           'does not exist')
            else:
                variables = parsed_args.args \
                    if len(parsed_args.args) > 0 \
                    else [k for k, v in self.app.secrets.items()]
            columns = ('Variable', 'Type', 'Prompt')
            data = (
                    [(k,
                      self.app.secrets.get_secret_type(k),
                      self.app.secrets.get_prompt(k))
                        for k, v in self.app.secrets.items()
                        if k in variables]
            )
        return columns, data


class SecretsGenerate(Command):
    """Generate values for secrets"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SecretsGenerate, self).get_parser(prog_name)
        parser.add_argument(
            '-U', '--unique',
            action='store_true',
            dest='unique',
            default=False,
            help="Generate unique values for each " +
            "type of secret (default: False)"
        )
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('generating secrets')
        self.app.secrets.read_secrets_and_descriptions()
        # If no secrets specified, default to all secrets
        to_change = parsed_args.args \
            if len(parsed_args.args) > 0 \
            else [k for k, v in self.app.secrets.items()]
        for k in to_change:
            t = self.app.secrets.get_secret_type(k)
            arguments = self.app.secrets.get_secret_arguments(k)
            v = generate_secret(secret_type=t,
                                unique=parsed_args.unique,
                                **arguments)
            if v is not None:
                self.LOG.debug("generated {} for {}".format(t, k))
                self.app.secrets.set_secret(k, v)


class SecretsSet(Command):
    """Set values manually for secrets"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SecretsSet, self).get_parser(prog_name)
        parser.add_argument(
            '--undefined',
            action='store_true',
            dest='undefined',
            default=False,
            help="Set values for undefined variables (default: False)"
        )
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('setting secrets')
        self.app.secrets.read_secrets_and_descriptions()
        if parsed_args.undefined:
            args = [k for k, v in self.app.secrets.items()
                    if v in [None, '']]
        else:
            args = parsed_args.args
        for arg in args:
            if '=' in arg:
                k, v = arg.split('=')
            else:
                k, v = arg, self.app.secrets.get_secret(arg, allow_none=True)
            k_type = self.app.secrets.get_type(k)
            if k_type is None:
                self.LOG.info('no description for {}'.format(k))
                raise RuntimeError('variable "{}" '.format(k) +
                                   'has no description')
            if '=' not in arg:
                v = prompt_string(
                    prompt=self.app.secrets.get_prompt(k),
                    default=v)
                if v is None:
                    self.LOG.info('no user input for "{}"'.format(k))
                    return None
            if v.startswith('@'):
                if v[1] == '~':
                    _path = os.path.expanduser(v[1:])
                else:
                    _path = v[1:]
                with open(_path, 'r') as f:
                    v = f.read().strip()
            elif v.startswith('!'):
                # >> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.  # noqa
                #    Severity: Low   Confidence: High
                #    Location: python_secrets/secrets.py:641
                p = run(v[1:].split(),
                        stdout=PIPE,
                        stderr=PIPE,
                        shell=False)
                v = p.stdout.decode('UTF-8').strip()
            self.LOG.debug('setting {}'.format(k))
            self.app.secrets.set_secret(k, v)


class SecretsGet(Command):
    """Get value associated with a secret"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '-C', '--content',
            action='store_true',
            dest='content',
            default=False,
            help="Get content if secret is a file path " +
            "(default: False)"
        )
        parser.add_argument('secret', nargs='?', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('get secret')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        if parsed_args.secret is not None:
            value = self.app.secrets.get_secret(
                parsed_args.secret, allow_none=True)
            if not parsed_args.content:
                print(value)
            else:
                if os.path.exists(value):
                    with open(value, 'r') as f:
                        content = f.read().replace('\n', '')
                    print(content)


class SecretsSend(Command):
    """
    Send secrets using GPG encrypted email.

    Arguments are USERNAME@EMAIL.ADDRESS and/or VARIABLE references.
    """

    LOG = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=None)
        self.refresh_token = None

    def get_parser(self, prog_name):
        parser = super(SecretsSend, self).get_parser(prog_name)
        parser.add_argument(
            '-T', '--refresh-token',
            action='store_true',
            dest='refresh_token',
            default=False,
            help="Refresh Google API Oauth2 token and exit (default: False)"
        )
        parser.add_argument(
            '--test-smtp',
            action='store_true',
            dest='test_smtp',
            default=False,
            help='Test Oauth2 SMTP authentication and exit ' +
                 '(default: False)'
        )
        parser.add_argument(
            '-H', '--smtp-host',
            action='store',
            dest='smtp_host',
            default='localhost',
            help="SMTP host (default: localhost)"
        )
        parser.add_argument(
            '-U', '--smtp-username',
            action='store',
            dest='smtp_username',
            default=None,
            help="SMTP authentication username (default: None)"
        )
        parser.add_argument(
            '-F', '--from',
            action='store',
            dest='smtp_sender',
            default='noreply@nowhere',
            help="Sender address (default: 'noreply@nowhere')"
        )
        parser.add_argument(
            '-S', '--subject',
            action='store',
            dest='smtp_subject',
            default='For Your Information',
            help="Subject line (default: 'For Your Information')"
        )
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('send secret(s)')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        # Attempt to get refresh token first
        orig_refresh_token = None
        self.refresh_token =\
            self.app.secrets.get_secret('google_oauth_refresh_token',
                                        allow_none=True)
        if parsed_args.refresh_token:
            orig_refresh_token = self.refresh_token
            self.LOG.debug('refreshing Google Oauth2 token')
        else:
            self.LOG.debug('sending secrets')
        if parsed_args.smtp_username is not None:
            username = parsed_args.smtp_username
        else:
            username = self.app.secrets.get_secret(
                'google_oauth_username')
        googlesmtp = GoogleSMTP(
            username=username,
            client_id=self.app.secrets.get_secret(
                'google_oauth_client_id'),
            client_secret=self.app.secrets.get_secret(
                'google_oauth_client_secret'),
            refresh_token=self.refresh_token
        )
        if parsed_args.refresh_token:
            new_refresh_token = googlesmtp.get_authorization()[0]
            if new_refresh_token != orig_refresh_token:
                self.app.secrets.set_secret('google_oauth_refresh_token',
                                            new_refresh_token)
            return None
        elif parsed_args.test_smtp:
            auth_string, expires_in = googlesmtp.refresh_authorization()
            googlesmtp.test_smtp(
                googlesmtp.generate_oauth2_string(
                    base64_encode=True))

        recipients = list()
        variables = list()
        for arg in parsed_args.args:
            if "@" in arg:
                recipients.append(arg)
            else:
                if self.app.secrets.get_secret(arg):
                    variables.append(arg)
        message = "The following secret{} {} ".format(
            "" if len(variables) == 1 else "s",
            "is" if len(variables) == 1 else "are"
            ) + "being shared with you:\n\n" + \
            "\n".join(
                ["{}='{}'".format(v, self.app.secrets.get_secret(v))
                 for v in variables]
            )
        # https://stackoverflow.com/questions/33170016/how-to-use-django-1-8-5-orm-without-creating-a-django-project/46050808#46050808  # noqa
        for recipient in recipients:
            googlesmtp.send_mail(parsed_args.smtp_sender,
                                 recipient,
                                 parsed_args.smtp_subject,
                                 message)
            self.LOG.info('sent encrypted secrets to {} '.format(recipient))


class SecretsPath(Command):
    """Return path to secrets file"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SecretsPath, self).get_parser(prog_name)
        default_environment = SecretsEnvironment().environment()
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('returning secrets path')
        e = SecretsEnvironment(environment=parsed_args.environment)
        e.requires_environment()
        print(e.secrets_file_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
