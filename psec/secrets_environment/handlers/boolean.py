# -*- coding: utf-8 -*-
"""
Boolean class.
"""

# Standard imports

# Local imports
from ..factory import (
    SecretFactory,
    SecretHandler,
)


@SecretFactory.register_handler(__name__.split('.')[-1])
class Boolean_c(SecretHandler):
    """
    Boolean string (`true` or `false`)
    """

    def generate_secret(self, **kwargs) -> str:
        """
        Cannot generate boolean strings.
        """
        return None


# vim: set ts=4 sw=4 tw=0 et :
