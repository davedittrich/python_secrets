# -*- coding: utf-8 -*-
"""
BASE64 encoded token class
"""

# Standard imports
import base64
import secrets

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


DEFAULT_SIZE = 32


@SecretFactory.register_handler(__name__.split('.')[-1])
class BASE64_Token_c(SecretHandler):
    """
    Random byte string
    """

    def generate_secret(
        self,
        unique=False,
        size=DEFAULT_SIZE,
        **kwargs,
    ) -> str:
        """
        Generate BASE64 encoded token of 'size' bytes.
        """
        return str(
            base64.b64encode(
                secrets.token_bytes(nbytes=size)
            ),
            encoding='utf-8'
        )


# vim: set ts=4 sw=4 tw=0 et :
