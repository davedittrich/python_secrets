# -*- coding: utf-8 -*-

import base64
import binascii
import hashlib
import logging
import os
import random
import uuid

from cliff.command import Command
from cliff.lister import Lister
from numpy.random import bytes as np_random_bytes
from .utils import redact
from xkcdpass import xkcd_password as xp


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


def generate_secret(key, type, unique=False, **kwargs):
    """Generate secret for the type of key"""
    if type == 'password':
        return generate_password(unique)
    elif type == 'consul_key':
        return generate_consul_key(unique)
    elif type == 'zookeeper_digest':
        return generate_zookeeper_digest(unique, **kwargs)
    elif type == 'uuid4':
        return generate_uuid4(unique, **kwargs)
    elif type == 'base64':
        return generate_random_base64(unique, **kwargs)
    else:
        raise TypeError("Secret type '{}' is not supported".format(type))


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
def generate_consul_key(unique=False):
    """Generate a consul key

    See: https://github.com/hashicorp/consul/blob/b3292d13fb8bbc8b14b2a1e2bbae29c6e105b8f4/command/keygen/keygen.go
    """  # noqa
    keybytes = np_random_bytes(16)
    ckey = binascii.b2a_base64(keybytes)
    return ckey.decode("utf-8").strip()


@Memoize
def generate_zookeeper_digest(unique=False, user=None, credential=None):
    """Generate a zookeeper-compatible digest from username and password"""
    assert user is not None, 'zk_digest(): user is not defined'
    assert credential is not None, 'zk_digest(): credential is not defined'
    return base64.b64encode(
        hashlib.sha1(user + ":" + credential).digest()
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
            v = generate_secret(k, t, unique=parsed_args.unique, **arguments)
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

# EOF
