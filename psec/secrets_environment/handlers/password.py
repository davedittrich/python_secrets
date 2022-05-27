# -*- coding: utf-8 -*-
"""
XKCD password class.
"""

# Standard imports
import secrets

# External imports
from xkcdpass import xkcd_password as xp
from xkcdpass.xkcd_password import CASE_METHODS

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)
from psec.utils import natural_number


# XKCD password defaults
# See: https://www.unix-ninja.com/p/your_xkcd_passwords_are_pwned
WORDS = 4
MIN_WORDS_LENGTH = 3
MAX_WORDS_LENGTH = 6
MIN_ACROSTIC_LENGTH = 3
MAX_ACROSTIC_LENGTH = 6
DELIMITER = '.'


@SecretFactory.register_handler(__name__.split('.')[-1])
class XKCD_Password_c(SecretHandler):
    """Simple (xkcd) password string"""

    def __init__(self):
        self.last_result = None

    def add_parser_arguments(self, parser):
        parser.add_argument(
            '--min-words-length',
            action='store',
            type=natural_number,
            dest='min_words_length',
            default=MIN_WORDS_LENGTH,
            help='Minimum word length for XKCD words list'
        )
        parser.add_argument(
            '--max-words-length',
            action='store',
            type=natural_number,
            dest='max_words_length',
            default=MAX_WORDS_LENGTH,
            help='Maximum word length for XKCD words list'
        )
        parser.add_argument(
            '--min-acrostic-length',
            action='store',
            type=natural_number,
            dest='min_acrostic_length',
            default=MIN_ACROSTIC_LENGTH,
            help='Minimum length of acrostic word for XKCD password'
        )
        parser.add_argument(
            '--max-acrostic-length',
            action='store',
            type=natural_number,
            dest='max_acrostic_length',
            default=MAX_ACROSTIC_LENGTH,
            help='Maximum length of acrostic word for XKCD password'
        )
        parser.add_argument(
            '--acrostic',
            action='store',
            dest='acrostic',
            default=None,
            help='Acrostic word for XKCD password'
        )
        parser.add_argument(
            '--delimiter',
            action='store',
            dest='delimiter',
            default=DELIMITER,
            help='Delimiter for XKCD password'
        )
        parser.add_argument(
            "-C", "--case",
            dest="case",
            type=str,
            metavar="CASE",
            choices=list(CASE_METHODS.keys()), default="alternating",
            help=(
                'Choose the method for setting the case of each '
                'word in the passphrase. '
                f"Choices: {list(CASE_METHODS.keys())}"
            )
        )
        return parser

    def generate_secret(self, **kwargs):
        """
        Generate an XKCD-style password string.

        For a note about the security issues with XKCD passwords,
        see: https://www.unix-ninja.com/p/your_xkcd_passwords_are_pwned
        """
        unique = kwargs.get('unique', False)
        case = kwargs.get('case', 'lower')
        acrostic = kwargs.get('acrostic', None)
        numwords = kwargs.get('numwords', WORDS)
        delimiter = kwargs.get('delimiter', DELIMITER)
        min_words_length = kwargs.get('min_words_length', MIN_WORDS_LENGTH)
        max_words_length = kwargs.get('max_words_length', MAX_WORDS_LENGTH)
        min_acrostic_length = kwargs.get(
            'min_acrostic_length',
            MIN_ACROSTIC_LENGTH,
        )
        max_acrostic_length = kwargs.get(
            'max_acrostic_length',
            MAX_ACROSTIC_LENGTH,
        )
        if numwords not in range(min_acrostic_length, max_acrostic_length):
            raise ValueError(
                "'numwords' must be between "
                f"{min_acrostic_length} and {max_acrostic_length}"
            )
        wordfile = kwargs.get('wordfile', None)

        if not unique and self.last_result:
            return self.last_result

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
        password = xp.generate_xkcdpassword(
            mywords,
            numwords=numwords,
            acrostic=acrostic,
            case=case,
            delimiter=delimiter,
        )
        if not unique:
            self.last_result = password
        return password


# vim: set ts=4 sw=4 tw=0 et :
