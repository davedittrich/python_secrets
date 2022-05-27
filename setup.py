#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Setup script for the `python_secrets' module.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://github.com/davedittrich/python_secrets

import codecs
import os

from setuptools import setup


# NOTE: The project name began as "python_secrets", but the shorter
# alias "psec" is used for the command. This causes a little confusion,
# but I don't want to completely rename the project at this time.
PROJECT = 'python_secrets'

long_description = (
    'Python CLI for decoupling secrets '
    '(passwords, API keys, etc.) from source code'
)
description_file = 'README.rst'

try:
    with open(description_file) as readme_file:
        long_description = readme_file.read()
except IOError:
    pass

try:
    with open('HISTORY.rst') as history_file:
        history = history_file.read().replace('.. :changelog:', '')
except IOError:
    history = ''


def get_contents(*args):
    """Get the contents of a file relative to the source distribution directory.""" # noqa
    with codecs.open(get_absolute_path(*args), 'r', 'UTF-8') as handle:
        return handle.read()


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


setup(
    setup_requires=['setuptools>=40.9.0', 'pip>=20.2.2'],
    python_requires='>=3.6',
    use_scm_version=True,
    install_requires=get_contents('requirements.txt'),
    long_description="\n".join([long_description, "", history]),
    long_description_content_type='text/x-rst',
    name=PROJECT,
    namespace_packages=[],
    # Alias the package name ("python_secrets") to the source directory
    # ("psec").
    packages=[
        'psec',
        'psec/cli',
        'psec/cli/environments',
        'psec/cli/groups',
        'psec/cli/secrets',
        'psec/cli/utils',
        'psec/secrets_environment/handlers',
        'psec/secrets_environment/factory',
        'psec/secrets_environment',
    ],
    package_dir={'python_secrets': 'psec'},
    test_suite='tests',
)

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
