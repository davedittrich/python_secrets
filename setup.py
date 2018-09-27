#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Setup script for the `python_secrets' module.
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
        long_description_content_type = 'text/x-rst'
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
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Security',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Installation/Setup',
        'Topic :: Utilities',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'python_secrets = python_secrets.main:main',
            'psec = python_secrets.main:main',
        ],
        'python_secrets': [
            'environments create = python_secrets.environments:EnvironmentsCreate',  # noqa
            'environments default = python_secrets.environments:EnvironmentsDefault',  # noqa
            'environments list = python_secrets.environments:EnvironmentsList',
            'environments path = python_secrets.environments:EnvironmentsPath',
            'environments tree = python_secrets.environments:EnvironmentsTree',
            'groups create = python_secrets.groups:GroupsCreate',
            'groups list = python_secrets.groups:GroupsList',
            'groups path = python_secrets.groups:GroupsPath',
            'groups show = python_secrets.groups:GroupsShow',
            'run = python_secrets.run:Run',
            'secrets describe = python_secrets.secrets:SecretsDescribe',
            'secrets generate = python_secrets.secrets:SecretsGenerate',
            'secrets get = python_secrets.secrets:SecretsGet',
            'secrets path = python_secrets.secrets:SecretsPath',
            'secrets send = python_secrets.secrets:SecretsSend',
            'secrets set = python_secrets.secrets:SecretsSet',
            'secrets show = python_secrets.secrets:SecretsShow',
            'template = python_secrets.template:Template',
            'utils myip = python_secrets.utils:MyIP',
            'utils tfoutput = python_secrets.utils:TfOutput',
        ],
    },
)
