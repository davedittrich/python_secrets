# -*- coding: utf-8 -*-
"""
String secret class.
"""
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler(__name__.split('.')[-1])
class String_c(SecretHandler):
    """Arbitrary string"""

    def generate_secret(self, **kwargs) -> str:
        """
        Strings are not generated.
        """
        return ''


# vim: set ts=4 sw=4 tw=0 et :
