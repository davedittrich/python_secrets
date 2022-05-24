# -*- coding: utf-8 -*-
"""
UUID4 secret class.
"""

# Standard imports
import uuid

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler(__name__.split('.')[-1])
class UUID4_c(SecretHandler):
    """
    UUID4 token
    """

    def generate_secret(self, **kwargs) -> str:
        """
        Generate a UUID4 string.
        """
        return str(uuid.uuid4())


# vim: set ts=4 sw=4 tw=0 et :
