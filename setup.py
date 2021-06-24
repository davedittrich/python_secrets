#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Setup script for the `python_secrets' module.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://github.com/davedittrich/python_secrets

import codecs
import os

from setuptools import find_packages, setup


# NOTE: The project name began as "python_secrets", but the shorter
# alias "psec" is used for the command. This causes a little confusion,
# but I don't want to completely rename the project at this time.
PROJECT = 'python_secrets'

long_description = ''
try:
    with open('README.rst') as readme_file:
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
    use_scm_version=True,
    include_package_data=True,
    install_requires=get_contents('requirements.txt'),
    long_description="\n".join([long_description, "", history]),
    long_description_content_type='text/x-rst',
    namespace_packages=[],
    # Alias the package name ("python_secrets") to the source directory
    # ("psec").
    package_dir={'python_secrets': 'psec'},
    packages=find_packages(exclude=['libs*']),
    test_suite='tests',
    zip_safe=False,
)
