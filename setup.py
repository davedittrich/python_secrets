#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Setup script for the `update-dotdee' package.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://github.com/davedittrich/python_secrets

import codecs
import os
import re

from setuptools import find_packages, setup


PROJECT = 'python_secrets'

try:
    with open('README.rst') as readme_file:
        long_description = readme_file.read()
except IOError:
        long_description = ''

try:
    with open('HISTORY.rst') as history_file:
        history = history_file.read().replace('.. :changelog:', '')
except IOError:
        history = ''


def get_contents(*args):
    """Get the contents of a file relative to the source distribution directory.""" # noqa
    with codecs.open(get_absolute_path(*args), 'r', 'UTF-8') as handle:
        return handle.read()


def get_version(*args):
    """Extract the version number from a Python module."""
    contents = get_contents(*args)
    metadata = dict(re.findall('__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


setup(
    name='python_secrets',
    version=get_version('python_secrets', '__init__.py'),
    description="Python CLI for managing secrets (passwords, API keys, etc)",
    long_description=long_description + "\n\n" + history,
    author="Dave Dittrich",
    author_email='dave.dittrich@gmail.com',
    url='https://github.com/davedittrich/python_secrets',
    packages=find_packages(),
    package_dir={'python_secrets':
                 'python_secrets'},
    include_package_data=True,
    install_requires=get_contents('requirements.txt'),
    license="Apache Software License",
    zip_safe=False,
    keywords='python_secrets',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'python_secrets = python_secrets.main:main',
            'psec = python_secrets.main:main',
        ],
        'python_secrets': [
            'secrets show = python_secrets.secrets:SecretsShow',
            'secrets set = python_secrets.secrets:SecretsSet',
            'secrets generate = python_secrets.secrets:SecretsGenerate',
            'groups list = python_secrets.groups:GroupsList',
            'groups show = python_secrets.groups:GroupsShow',
        ],
    },
)
