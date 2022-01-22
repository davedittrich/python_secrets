# -*- coding: utf-8 -*-

"""
Exception classes.
"""


class EnvironmentsError(Exception):
    pass


class BasedirNotFoundError(EnvironmentsError):
    pass


class InvalidBasedirError(EnvironmentsError):
    pass


class SecretsError(Exception):
    pass


class SecretNotFoundError(SecretsError):
    pass


class InvalidDescriptionsError(SecretsError):
    pass


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
