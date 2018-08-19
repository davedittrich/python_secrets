import base64
import binascii
import crypt
import hashlib
import logging
import os
import random
import secrets
import uuid

from cliff.command import Command
from cliff.lister import Lister
from numpy.random import bytes as np_random_bytes
from .utils import redact
from xkcdpass import xkcd_password as xp
from .google_oauth2 import GoogleSMTP

SECRET_TYPES = [
        {'Type': 'password', 'Description': 'Simple password string'},
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
        hashlib.sha1(user + ":" + credential).digest()
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
def generate_random_base64(unique=False, size=2**5 + 1):
    """Generate random base64 encoded string of 'size' bytes"""
    return base64.b64encode(os.urandom(size))


class SecretsShow(Lister):
    """List the contents of the secrets file"""

    log = logging.getLogger(__name__)

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
        self.log.debug('listing secrets')
        variables = []
        if parsed_args.args_group:
            for g in parsed_args.args:
                variables.extend(
                    [v for v in self.app.get_items_from_group(g)]
                 )
        else:
            variables = parsed_args.args \
                if len(parsed_args.args) > 0 \
                else [k for k in self.app.secrets.keys()]
        columns = ('Variable', 'Value')
        data = (
                [(k, redact(v, parsed_args.redact))
                    for k, v in self.app.secrets.items() if k in variables]
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

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SecretsGenerate, self).get_parser(prog_name)
        parser.add_argument(
            '-U', '--unique',
            action='store_true',
            dest='unique',
            default=False,
            help="Generate unique secrets for each " +
            "type of secret (default: False)"
        )
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('generating secrets')
        to_change = parsed_args.args \
            if len(parsed_args.args) > 0 \
            else [i['Variable'] for i in self.app.secrets_descriptions]

        for k in to_change:
            t = self.app.get_secret_type(k)
            arguments = self.app.get_secret_arguments(k)
            v = generate_secret(secret_type=t,
                                unique=parsed_args.unique,
                                **arguments)
            self.log.debug("generated {} for {}".format(t, k))
            self.app.set_secret(k, v)


class SecretsSet(Command):
    """Set values manually for secrets"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SecretsSet, self).get_parser(prog_name)
        parser.add_argument('args', nargs='*', default=None)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('setting secrets')
        for kv in parsed_args.args:
            k, v = kv.split('=')
            try:
                description = next(  # noqa
                        (item for item
                            in self.app.secrets_descriptions
                            if item["Variable"] == k))
                # TODO(dittrich): validate description['Type']
            except StopIteration:
                self.log.info('no description for {}'.format(k))
            else:
                self.log.debug('setting {}'.format(k))
                self.app.set_secret(k, v)


class SecretsSend(Command):
    """
    Send secrets using GPG encrypted email.

    Arguments are USERNAME@EMAIL.ADDRESS and/or VARIABLE references.
    """

    log = logging.getLogger(__name__)

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
            self.log.debug('refreshing Google Oauth2 token')
        else:
            self.log.debug('sending secrets')
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

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
