# -*- coding: utf-8 -*-

"""
Generic modular secrets configuration file management.

The :mod:`psec` module provides one class that
implements a mechanism for generating, prompting for, or
retrieving "secrets" (passwords, API tokens, etc.) that
are required for access control mechanisms in applications
or services.

- :class:`Python_Secrets` implements the Python API of the ``psec``
  program ...

"""

# Standard libraries.

# External dependencies.
from property_manager import PropertyManager
# TODO(dittrich): Finish this...
# from property_manager import (
#     PropertyManager,
#     cached_property,
#     mutable_property,
#     required_property,
# )


class Python_Secrets(PropertyManager):

    """
    The :class:`Python_Secrets` class implements the Python
    API of `psec`.

    """

    def __init__(self):
        pass

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
