# -*- coding: utf-8 -*-
"""
DIGEST-SHA256 secret class.
"""

# Standard imports
import base64
import hashlib

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler(__name__.split('.')[-1])
class DIGEST_SHA256_c(SecretHandler):
    """
    DIGEST-SHA256 (user:pass) digest
    """

    def generate_secret(self, user=None, credential=None, **kwargs) -> str:
        """
        Generate a DIGEST-SHA256 (user:pass) digest
        """
        if user is None:
            raise RuntimeError('[-] user is not defined')
        if credential is None:
            raise RuntimeError('[-] credential is not defined')
        return base64.b64encode(
            hashlib.sha256(
                user + ":" + credential
            ).digest()
        ).strip()


# vim: set ts=4 sw=4 tw=0 et :
