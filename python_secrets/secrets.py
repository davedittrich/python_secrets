import base64
import binascii
import crypt
import errno
import hashlib
import logging
import os
import random
import secrets
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
HOME = os.path.expanduser('~')
CWD = os.getcwd()
SECRETS_ROOT = os.path.join(
    HOME, "secrets" if '\\' in HOME else ".secrets")
DEFAULT_MODE = 0o710


def copyanything(src, dst):
    try:
        copytree(src, dst)
    except FileExistsError as exc:
        pass
    except OSError as exc:  # python >2.5
        if exc.errno == errno.ENOTDIR:
            copy(src, dst)
        else:
            raise


class SecretsEnvironment(object):
    """Class for handling secrets environment metadata"""

    LOG = logging.getLogger(__name__)

    def __init__(self,
                 environment=None,
                 secrets_root=SECRETS_ROOT,
                 secrets_file="secrets.yml",
                 create_root=True,
                 defer_loading=True,
                 export_env_vars=False,
                 env_var_prefix=None,
                 source=None):
        self._environment = environment \
            if environment is not None else os.path.basename(CWD)
        self._secrets_root = secrets_root
        self._secrets_file = secrets_file
        self._secrets_descriptions = "{}.d".format(
            os.path.splitext(self._secrets_file)[0])
        # Ensure root directory exists in which to create secrets
        # environments?
        if not self.root_path_exists():
            if create_root:
                self.root_path_create()
            else:
                raise RuntimeError('Directory {} '.format(self.root_path()) +
                                   'does not exist and create_root=False')
        self.export_env_vars = export_env_vars
        self.env_var_prefix = env_var_prefix
        if source is not None:
            self.clone_from(source)
        self._secrets = dict()
        self._descriptions = dict()
        self._changed = False
        self._groups = []

    def root_path(self):
        """Returns the absolute path to secrets root directory"""
        return self._secrets_root

    def root_path_exists(self):
        """Return whether secrets root directory exists"""
        return os.path.exists(self.root_path())

    def root_path_create(self, mode=DEFAULT_MODE):
        """Create secrets root directory"""
        os.mkdir(self._secrets_root, mode=mode)

    def environment_path(self):
        """Returns the absolute path to secrets environment directory"""
        return os.path.join(self._secrets_root, self._environment)

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
                    self._environment))

    def secrets_file_path(self):
        """Returns the absolute path to secrets file"""
        if self._environment is None:
            return os.path.join(self._secrets_root, self._secrets_file)
        else:
            return os.path.join(self._secrets_root,
                                self._environment,
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
            self.environment_path_create(mode=mode)
        if not self.descriptions_path_exists():
            os.mkdir(self.descriptions_path(), mode=mode)

    def keys(self):
        """Return the keys to the secrets dictionary"""
        return [s for s in self._secrets.keys()]

    def items(self):
        """Return the items from the secrets dictionary."""
        return self._secrets.items()

    def get_secret(self, secret):
        """Get the value of secret

        :param secret: :type: string
        :return: value of secret
        """
        return self._secrets[secret]

    def get_secret_export(self, secret):
        """Get the specified environment variable for exporting secret

        :param secret: :type: string
        :return: environment variable for exporting secret
        """
        # TODO(dittrich): Create a map after reading (more efficient)
        for group in self._descriptions.keys():
            for i in self._descriptions[group]:
                if i['Variable'] == secret:
                    return i.get('Export')
        return None

    def _set_secret(self, secret, value):
        """Set secret to value and export environment variable

                :param secret: :type: string
                :param value: :type: string
                :return:
                """
        self._secrets[secret] = value
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
        self._set_secret(secret, value)
        self._changed = True

    def get_type(self, variable):
        """Return type for variable or None if no description"""
        # TODO(dittrich): Create a map after reading (more efficient)
        for group in self._descriptions.keys():
            for i in self._descriptions[group]:
                if i['Variable'] == variable:
                    return i['Type']
        return None

    def changed(self):
        """Return boolean reflecting changed secrets."""
        return self._changed

    def read_secrets_and_descriptions(self):
        """Read secrets descriptions and secrets."""
        self.read_secrets_descriptions()
        self.read_secrets(from_descriptions=True)

    def read_secrets(self, from_descriptions=False):
        """
        Load the current secrets from .yml file

        If no secrets have been set yet and from_descriptions is True,
        return a dictionary compromised of the keys from the
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

    def read_secrets_descriptions(self):
        """Load the descriptions of groups of secrets from a .d directory"""
        groups_dir = self.descriptions_path()
        if os.path.exists(groups_dir):
            # Ignore .order file and any other non-YAML file extensions
            extensions = ['yml', 'yaml']
            file_names = [fn for fn in os.listdir(groups_dir)
                          if any(fn.endswith(ext) for ext in extensions)]
            self._groups = [os.path.splitext(fn) for fn in file_names]
            self.LOG.debug('reading secrets descriptions from {}'.format(
                groups_dir))
            try:
                # Iterate over files in directory, loading them into
                # dictionaries as dictionary keyed on group name.
                for fname in file_names:
                    group = os.path.splitext(fname)[0]
                    with open(os.path.join(groups_dir, fname), 'r') as f:
                        data = yaml.safe_load(f)
                    self._descriptions[group] = data
            except Exception:
                self.LOG.info('no secrets descriptions files found')
        else:
            self.LOG.info('secrets descriptions directory not found')

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

    def get_parser(self, prog_name):
        parser = super(SecretsShow, self).get_parser(prog_name)
        # Sorry for the double-negative, but it works better
        # this way for the user as a flag and to have a default
        # of redacting (so they need to turn it off)
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
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('showing secrets')
        self.app.secrets.read_secrets_and_descriptions()
        variables = []
        if parsed_args.args_group:
            for g in parsed_args.args:
                variables.extend(
                    [v for v in self.app.secrets.get_items_from_group(g)]
                 )
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

    def get_parser(self, prog_name):
        parser = super(SecretsDescribe, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('describing secrets')
        columns = [k.title() for k in SECRET_TYPES[0].keys()]
        data = [[v for k, v in i.items()] for i in SECRET_TYPES]
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
                k, v = arg, self.app.secrets.get_secret(arg)
            k_type = self.app.secrets.get_type(k)
            if k_type is None:
                self.LOG.info('no description for {}'.format(k))
                raise RuntimeError('variable "{}" '.format(k) +
                                   'has no description')
            if k_type == 'string':
                if '=' not in arg:
                    v = prompt_string(prompt=k, default=v)
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
        # Attempt to get refresh token first
        orig_refresh_token = None
        try:
            self.refresh_token = self.app.secrets[
                "google_oauth_refresh_token"]
        except KeyError:
            pass
        if parsed_args.refresh_token:
            orig_refresh_token = self.refresh_token
            self.LOG.debug('refreshing Google Oauth2 token')
        else:
            self.LOG.debug('sending secrets')
        googlesmtp = GoogleSMTP(
            parsed_args.smtp_username,
            client_id=self.app.secrets['google_oauth_client_id'],
            client_secret=self.app.secrets['google_oauth_client_secret'],
            refresh_token=self.refresh_token
        )
        if parsed_args.refresh_token:
            new_refresh_token = googlesmtp.get_authorization()[0]
            if new_refresh_token != orig_refresh_token:
                self.app.set_secret('google_oauth_refresh_token',
                                    new_refresh_token)
            return None
        elif parsed_args.test_smtp:
            auth_string = googlesmtp.refresh_authorization()
            googlesmtp.test_smtp(self, auth_string)

        recipients = list()
        variables = list()
        for arg in parsed_args.args:
            if "@" in arg:
                recipients.append(arg)
            else:
                if arg not in self.app.secrets:
                    raise NameError(
                        "Secret '{}' is not defined".format(arg))
                variables.append(arg)
        message = "The following secret{} {} ".format(
            "" if len(variables) == 1 else "s",
            "is" if len(variables) == 1 else "are"
            ) + "being shared with you:\n\n" + \
            "\n".join(
                ['{}={}'.format(v, self.app.secrets[v]) for v in variables]
            )
        # https://stackoverflow.com/questions/33170016/how-to-use-django-1-8-5-orm-without-creating-a-django-project/46050808#46050808
        for recipient in recipients:
            googlesmtp.send_mail(parsed_args.smtp_sender,
                                 recipient,
                                 parsed_args.smtp_subject,
                                 message)


class SecretsPath(Command):
    """Return path to secrets file"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SecretsPath, self).get_parser(prog_name)
        default_environment = self.app.options.environment
        parser.add_argument('environment',
                            nargs='?',
                            default=default_environment)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('returning secrets path')
        e = parsed_args.environment
        print(SecretsEnvironment(environment=e).secrets_file_path())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
