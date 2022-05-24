# -*- coding: utf-8 -*-
"""
Hex token secret class.
"""

# Standard imports
import secrets

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler(__name__.split('.')[-1])
class Token_Hex32_c(SecretHandler):
    """
    32-bit hexadecimal token
    """

    def generate_secret(self, nbytes=32, **kwargs) -> str:
        """
        Generate a 32-bit hexadecimal token.
        """
        return secrets.token_hex(nbytes=nbytes)


# vim: set ts=4 sw=4 tw=0 et :
