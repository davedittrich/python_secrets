# -*- coding: utf-8 -*-
"""
String secret class.
"""
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler('string')
class String_c(SecretHandler):

    def generate_secret(self, **kwargs) -> str:
        """
        Strings are not generated.
        #FIXME: But I could use Bullet! ;)
        """
        return ''


# vim: set ts=4 sw=4 tw=0 et :
