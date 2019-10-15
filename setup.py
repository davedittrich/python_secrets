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
    name='psec',
    pbr=True,

    setup_requires=['pbr>=1.9', 'setuptools>=17.1'],

    description="Python CLI for managing secrets (passwords, API keys, etc)",
    long_description=long_description + "\n\n" + history,

    author="Dave Dittrich",
    author_email='dave.dittrich@gmail.com',

    url='https://github.com/davedittrich/python_secrets',
    download_url='https://github.com/davedittrich/python_secrets/tarball/master',  # noqa

    namespace_packages=[],
    packages=find_packages(),
    package_dir={'psec':
                 'psec'},
    include_package_data=True,

    python_requires='>=3.6',
    install_requires=get_contents('requirements.txt'),

    license="Apache Software License",
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
    scripts=['bin/psec'],
    entry_points={
        'console_scripts': [
            'psec = psec.main:main',
        ],
        'psec': [
            'environments create = psec.environments:EnvironmentsCreate',  # noqa
            'environments default = psec.environments:EnvironmentsDefault',  # noqa
            'environments delete = psec.environments:EnvironmentsDelete',
            'environments list = psec.environments:EnvironmentsList',
            'environments path = psec.environments:EnvironmentsPath',
            'environments rename = psec.environments:EnvironmentsRename',  # noqa
            'environments tree = psec.environments:EnvironmentsTree',
            'groups create = psec.groups:GroupsCreate',
            'groups list = psec.groups:GroupsList',
            'groups path = psec.groups:GroupsPath',
            'groups show = psec.groups:GroupsShow',
            'run = psec.run:Run',
            'secrets describe = psec.secrets:SecretsDescribe',
            'secrets generate = psec.secrets:SecretsGenerate',
            'secrets get = psec.secrets:SecretsGet',
            'secrets path = psec.secrets:SecretsPath',
            'secrets send = psec.secrets:SecretsSend',
            'secrets set = psec.secrets:SecretsSet',
            'secrets show = psec.secrets:SecretsShow',
            'ssh config = psec.ssh:SSHConfig',
            'ssh known-hosts add = psec.ssh:SSHKnownHostsAdd',
            'ssh known-hosts extract = psec.ssh:SSHKnownHostsExtract',
            'ssh known-hosts remove = psec.ssh:SSHKnownHostsRemove',
            'template = psec.template:Template',
            'utils myip = psec.utils:MyIP',
            'utils set-aws-credentials = psec.utils:SetAWSCredentials',  # noqa
            'utils tfstate backend = psec.utils:TfBackend',
            'utils tfstate output = psec.utils:TfOutput',
        ],
    },
    zip_safe=False,
)
