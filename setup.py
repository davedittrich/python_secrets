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


def get_version(*args):
    """Extract the version number from a Python module."""
    contents = get_contents(*args)
    metadata = dict(re.findall(r'__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


setup(
    name='psec',
    pbr=True,

    setup_requires=['pbr>=5.4.5', 'setuptools>=17.1'],

    description="Python CLI for managing secrets (passwords, API keys, etc)",
    long_description="\n".join([long_description, "", history]),
    long_description_content_type='text/x-rst',

    author="Dave Dittrich",
    author_email='dave.dittrich@gmail.com',

    url='https://github.com/davedittrich/python_secrets',
    download_url='https://github.com/davedittrich/python_secrets/tarball/master',  # noqa

    namespace_packages=[],
    packages=find_packages(exclude=['libs*']),
    package_dir={'psec': 'psec'},
    include_package_data=True,
    # exclude_package_data={'psec': ['libs']},

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
        'Programming Language :: Python :: 3.8',
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
            'environments create = psec.environments.create:EnvironmentsCreate',  # noqa
            'environments default = psec.environments.default:EnvironmentsDefault',  # noqa
            'environments delete = psec.environments.delete:EnvironmentsDelete',  # noqa
            'environments list = psec.environments.list:EnvironmentsList',
            'environments path = psec.environments.path:EnvironmentsPath',
            'environments rename = psec.environments.rename:EnvironmentsRename',  # noqa
            'environments tree = psec.environments.tree:EnvironmentsTree',
            'groups create = psec.groups.create:GroupsCreate',
            'groups delete = psec.groups.delete:GroupsDelete',
            'groups list = psec.groups.list:GroupsList',
            'groups path = psec.groups.path:GroupsPath',
            'groups show = psec.groups.show:GroupsShow',
            'run = psec.run:Run',
            'secrets backup = psec.secrets.backup:SecretsBackup',
            'secrets create = psec.secrets.create:SecretsCreate',
            'secrets delete = psec.secrets.delete:SecretsDelete',
            'secrets describe = psec.secrets.describe:SecretsDescribe',
            'secrets generate = psec.secrets.generate:SecretsGenerate',
            'secrets get = psec.secrets.get:SecretsGet',
            'secrets path = psec.secrets.path:SecretsPath',
            'secrets restore = psec.secrets.restore:SecretsRestore',
            'secrets send = psec.secrets.send:SecretsSend',
            'secrets set = psec.secrets.set:SecretsSet',
            'secrets show = psec.secrets.show:SecretsShow',
            'ssh config = psec.ssh:SSHConfig',
            'ssh known-hosts add = psec.ssh:SSHKnownHostsAdd',
            'ssh known-hosts extract = psec.ssh:SSHKnownHostsExtract',
            'ssh known-hosts remove = psec.ssh:SSHKnownHostsRemove',
            'template = psec.template:Template',
            'utils myip = psec.utils.myip:MyIP',
            'utils myip methods = psec.utils.myip:MyIPMethods',
            'utils netblock = psec.utils.netblock:Netblock',
            'utils set-aws-credentials = psec.utils.set_aws_credentials:SetAWSCredentials',  # noqa
            'utils tfstate backend = psec.utils.tfbackend:TfBackend',
            'utils tfstate output = psec.utils.tfoutput:TfOutput',
            'utils yaml-to-json = psec.utils.yaml_to_json:YAMLToJSON',
        ],
    },
    zip_safe=False,
)
