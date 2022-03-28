#!/usr/bin/env python

"""
test_exceptions
---------------

Tests for exceptions.
"""

import pytest
import unittest


from psec import exceptions as exc


environment_exceptions = [
    exc.PsecEnvironmentAlreadyExistsError,
    exc.PsecEnvironmentNotFoundError,
]
basedir_exceptions = [
    exc.BasedirNotFoundError,
    exc.InvalidBasedirError,
]
secret_exceptions = [
    exc.SecretNotFoundError,
]
exceptions = (
    environment_exceptions
    + basedir_exceptions
    + secret_exceptions
    + [exc.DescriptionsError]
)


@pytest.mark.parametrize('exc', exceptions)
class Test_Exceptions(object):

    def test_exception_with_no_msg(self, exc):
        with pytest.raises(exc) as exc_info:
            raise exc()
        assert exc_info.type is exc
        assert str(exc_info.value.args[0]) == exc.__doc__

    def test_base_exception_with_msg(self, exc):
        with pytest.raises(exc) as exc_info:
            raise exc(msg='MESSAGE')
        assert exc_info.type is exc
        assert str(exc_info.value.args[0]) == 'MESSAGE'


@pytest.mark.parametrize('exc', environment_exceptions)
class Test_Environment_Exceptions(object):

    def test_environment_exceptions(self, exc):
        with pytest.raises(exc) as exc_info:
            raise exc(environment='ENVIRONMENT')
        assert exc_info.type is exc
        assert str(exc_info.value.environment) == 'ENVIRONMENT'


@pytest.mark.parametrize('exc', basedir_exceptions)
class Test_Basedir_Exceptions(object):

    def test_basedir_exceptions(self, exc):
        with pytest.raises(exc) as exc_info:
            raise exc(basedir='BASEDIR')
        assert exc_info.type is exc
        assert str(exc_info.value.basedir) == 'BASEDIR'


@pytest.mark.parametrize("exc", secret_exceptions)
class Test_Secret_Exceptions(object):

    def test_secret_exceptions(self, exc):
        with pytest.raises(exc) as exc_info:
            raise exc(secret='SECRET')
        assert exc_info.type is exc
        assert str(exc_info.value.secret) == 'SECRET'


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
