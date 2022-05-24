# -*- coding: utf-8 -*-
"""
Random bytes token class
"""

# Standard imports
import secrets

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


DEFAULT_SIZE = 18


@SecretFactory.register_handler(__name__.split('.')[-1])
class Random_Bytes_c(SecretHandler):
    """
    Random byte string
    """

    def generate_secret(self, unique=False, size=DEFAULT_SIZE, **kwargs) -> str:
        """
        Generate random byte string of 'size' bytes
        """
        return secrets.token_bytes(nbytes=size)


# vim: set ts=4 sw=4 tw=0 et :
