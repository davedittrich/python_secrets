# -*- coding: utf-8 -*-

"""
``psec`` exception classes.
"""


class PsecBaseException(Exception):
    """Base class for psec exceptions"""
    # This base class uses the __doc__ string of subclasses as the default
    # message. To customize the message, pass it to ``__init__()`` as
    # the ``msg`` argument.
    #
    # Subclasses are responsible for adding any additional information by
    # overloading the own ``__str__()`` method.
    #
    # Don't raise this exception directly.
    #
    def __init__(self, *args, msg=None, **kwargs):
        super().__init__(msg or self.__doc__, *args, **kwargs)
        self.msg = self.__doc__

    def __str__(self):
        return str(self.msg)


class PsecEnvironmentError(PsecBaseException):
    """Environment error"""
    # Subclasses should pass the environment name as the
    # ``environment`` keyword argument to ``__init__()``.
    #
    def __init__(self, *args, **kwargs):
        self.environment = kwargs.pop('environment', None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        addendum = (
            f": {self.environment}"
            if self.environment is not None
            else ''
        )
        return str(self.__doc__ + addendum)


class PsecEnvironmentAlreadyExistsError(PsecEnvironmentError):
    """Environment already exists"""


class PsecEnvironmentNotFoundError(PsecEnvironmentError):
    """Environment does not exist"""


class BasedirError(PsecBaseException):
    """Base directory error"""
    # Subclasses should pass the environment name as the
    # ``basedir`` keyword argument to ``__init__()``.
    #
    def __init__(self, *args, **kwargs):
        self.basedir = kwargs.pop('basedir', None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        addendum = (
            f": {self.basedir}"
            if self.basedir is not None
            else ''
        )
        return str(self.__doc__ + addendum)


class BasedirNotFoundError(BasedirError):
    """Basedir does not exist"""


class InvalidBasedirError(BasedirError):
    """Basedir is not valid"""


class SecretsError(PsecBaseException):
    """Secrets exception base class"""
    # Subclasses should pass the variable name as the
    # ``secret`` keyword argument to ``__init__()``.
    #
    def __init__(self, *args, **kwargs):
        self.secret = kwargs.pop('secret', None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        addendum = (
            f": {self.secret}"
            if self.secret is not None
            else ''
        )
        return str(self.__doc__ + addendum)


class SecretNotFoundError(SecretsError):
    """Secret not found"""


class SecretTypeNotFoundError(SecretsError):
    """Secret type not found"""


class DescriptionsError(PsecBaseException):
    """Secrets descriptions exception base class"""


class InvalidDescriptionsError(DescriptionsError):
    """Invalid secrets descriptions"""


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
