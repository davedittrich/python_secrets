#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_secrets_environment
------------------------

Tests for `psec.secrets_environment` module.
"""

import unittest
import os
import sys

from pathlib import Path
from unittest.mock import patch

from psec.secrets_environment import SecretsEnvironment
from psec.utils import (
    get_default_environment,
    get_local_default_file,
)


HOST = 'example.com'
HOME = os.path.expanduser('~')
TESTENV = 'pytest'
SECRETS_SUBDIR = 'pytest'
KEYS_SUBDIR = 'keys'


def secrets_dir(env=os.getenv('D2_ENVIRONMENT', None),
                basedir=os.getenv('D2_SECRETS_BASEDIR', None)):
    if env is not None:
        env_str = str(env)
    else:
        cwd = os.getcwd()
        default_file = Path(cwd) / '.python_secrets_environment'
        if os.path.exists(default_file):
            with open(default_file, 'r') as f:
                env_str = f.read().strip()
        else:
            env_str = os.path.basename(cwd)
    if basedir is None:
        basedir = Path(HOME) / (
            'secrets' if sys.platform.startswith('win') else '.secrets'
        )
    return Path(basedir) / env_str


def keys_dir(secrets_dir=secrets_dir(),
             keys_subdir=KEYS_SUBDIR):
    return Path(secrets_dir) / keys_subdir


def keys_with_host_dir(keys_dir=keys_dir(), host=HOST):
    return Path(keys_dir) / host


class Test_SecretsEnvironment_general(unittest.TestCase):

    def setUp(self):
        self.host = HOST
        with patch.dict('os.environ'):
            for v in ['D2_ENVIRONMENT', 'D2_SECRETS_BASEDIR']:
                try:
                    del os.environ[v]
                except KeyError as e:  # noqa
                    pass
        self.secrets_env = SecretsEnvironment(create_root=True)

    def tearDown(self):
        self.secrets_env = None

    @unittest.skipIf(sys.platform.startswith("win"), "not for Windows")
    def test_skip_if_windows(self):
        """Skip if not running on Windows"""
        pass

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_skip_unless_windows(self):
        """Skip if running on Windows"""
        pass

    def test_environment_patchtest(self):
        """Sample test patching environment"""
        self.env = patch.dict('os.environ', {'hello': 'world'})
        with self.env:
            self.assertEqual(os.environ['hello'], 'world')

    def test_environment_path_nosubdir_host(self):
        """Rejects null host"""
        self.assertRaises(
            RuntimeError,
            self.secrets_env.get_environment_path,
            host=self.host
        )

    def test_environment_path_subdir_leadingslash(self):
        """Rejects subdirectory with leading slash"""
        self.assertRaises(
            RuntimeError,
            self.secrets_env.get_environment_path,
            subdir="/keys"
        )

    def test_environment_path_subdir_trailingslash(self):
        """Rejects subdirectory with training slash"""
        self.assertRaises(
            RuntimeError,
            self.secrets_env.get_environment_path,
            subdir="keys/"
        )


class Test_SecretsEnvironment_no_env_vars(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.host = HOST
        self.keys_subdir = KEYS_SUBDIR
        self.secrets_env = None
        with patch.dict('os.environ'):
            for v in ['D2_ENVIRONMENT', 'D2_SECRETS_BASEDIR']:
                try:
                    del os.environ[v]
                except KeyError as e:  # noqa
                    pass
            self.secrets_env = SecretsEnvironment(create_root=True)

    def tearDown(self):
        pass

    def test_no_D2_ENVIRONMENT(self):
        """Asserting D2_ENVIRONMENT not set in environment"""
        self.assertIsNone(os.environ.get('D2_ENVIRONMENT'))

    def test_environment_path(self):
        assert type(self.secrets_env) is not type(str)
        env_path = self.secrets_env.get_environment_path()
        self.assertEqual(env_path, secrets_dir())

    def test_environment_path_subdir(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(subdir=self.keys_subdir),
            keys_dir()
        )

    def test_environment_path_subdir_host(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(
                subdir=KEYS_SUBDIR,
                host=self.host),
            keys_with_host_dir(host=self.host)
        )


class Test_SecretsEnvironment_with_env_vars(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.host = HOST
        self.keys_subdir = KEYS_SUBDIR
        self.envname = TESTENV
        self.basedir = Path(HOME) / (
           SECRETS_SUBDIR
           if sys.platform.startswith('win')
           else '.' + SECRETS_SUBDIR
        )
        self.secrets_env = None
        with patch.dict('os.environ'):
            os.environ['D2_ENVIRONMENT'] = str(self.envname)
            os.environ['D2_SECRETS_BASEDIR'] = str(self.basedir)
            self.secrets_dir = secrets_dir(
                env=self.envname,
                basedir=self.basedir
            )
            self.keys_dir = keys_dir(secrets_dir=self.secrets_dir)
            self.keys_with_host_dir = keys_with_host_dir(
                keys_dir=self.keys_dir,
                host=self.host
            )
            self.secrets_env = SecretsEnvironment(
                environment=self.envname,
                create_root=True
            )  # noqa

    def tearDown(self):
        pass

    def test_environment(self):
        self.assertEqual(
            str(self.secrets_env),
            self.envname
        )

    def test_environment_path(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(),
            self.secrets_dir
        )

    def test_environment_path_subdir(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(subdir=KEYS_SUBDIR),
            self.keys_dir
        )

    def test_environment_path_subdir_host(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(
                subdir=KEYS_SUBDIR,
                host=HOST),
            self.keys_with_host_dir
        )


class Test_SecretsEnvironment_args(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.host = HOST
        self.keys_subdir = KEYS_SUBDIR
        self.envname = TESTENV
        self.basedir = Path(HOME) / (
            SECRETS_SUBDIR
            if sys.platform.startswith('win')
            else '.' + SECRETS_SUBDIR
        )
        self.secrets_env = None
        with patch.dict('os.environ'):
            for v in ['D2_ENVIRONMENT', 'D2_SECRETS_BASEDIR']:
                try:
                    del os.environ[v]
                except KeyError as e:  # noqa
                    pass
            self.secrets_dir = secrets_dir(env=self.envname,
                                           basedir=self.basedir)
            self.keys_dir = keys_dir(secrets_dir=self.secrets_dir)
            self.keys_with_host_dir = keys_with_host_dir(
                keys_dir=self.keys_dir,
                host=self.host
            )
            self.secrets_env = SecretsEnvironment(
                environment=self.envname,
                secrets_basedir=self.basedir,
                create_root=True,
            )

    def tearDown(self):
        pass

    def test_no_D2_ENVIRONMENT(self):
        """Asserting D2_ENVIRONMENT not set in environment"""
        self.assertIsNone(os.environ.get('D2_ENVIRONMENT'))

    def test_environment_path(self):
        self.assertEqual(self.secrets_env.get_environment_path(),
                         self.secrets_dir)

    def test_environment_path_subdir(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(subdir=self.keys_subdir),
            self.keys_dir)

    def test_environment_path_subdir_host(self):
        self.assertEqual(
            self.secrets_env.get_environment_path(
                subdir=KEYS_SUBDIR,
                host=self.host),
            self.keys_with_host_dir)


class Test_SecretsEnvironment_defaults(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_default_environment_no_default_file(self):
        cwd = os.getcwd()
        self.assertEqual(
            get_default_environment(cwd=cwd),
            os.path.basename(cwd)
        )

    def test_get_default_environment_default_file(self):
        tmp_dir = '/tmp'
        new_env_file = get_local_default_file(cwd=tmp_dir)
        self.assertEqual(
            new_env_file,
            Path(tmp_dir) / '.python_secrets_environment'
        )
        with open(new_env_file, 'w') as f_out:
            f_out.write(TESTENV)
        default_env = get_default_environment(cwd=tmp_dir)  # noqa
        os.unlink(new_env_file)
        self.assertEqual(default_env, TESTENV)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
