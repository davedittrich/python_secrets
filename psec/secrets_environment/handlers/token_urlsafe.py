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
class Token_URLsafe_c(SecretHandler):
    """
    32-bit URL-safe token
    """

    def generate_secret(self, nbytes=32, **kwargs) -> str:
        """
        Generate a 32-bit URL-safe token.
        """
        return secrets.token_urlsafe(nbytes=nbytes)


# vim: set ts=4 sw=4 tw=0 et :
