# -*- coding: utf-8 -*-
"""
crypt_6 secret class.
"""

# Standard imports
import crypt

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler(__name__)
class Crypt_6_c(SecretHandler):
    """
        crypt() style SHA512 ("$6$") digest
    """

    def generate_secret(
        self,
        unique=False,
        password=None,
        salt=None,
        **kwargs,
    ):
        """
        Generate a crypt() style SHA512 ("$6$") digest
        """
        if password is None:
            raise RuntimeError("[-] 'password' is not defined")
        if salt is None:
            salt = crypt.mksalt(crypt.METHOD_SHA512)
        return crypt.crypt(password, salt)


# vim: set ts=4 sw=4 tw=0 et :
