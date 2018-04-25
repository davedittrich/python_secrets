==============
python_secrets
==============

.. image:: https://img.shields.io/pypi/v/python_secrets.svg
        :target: https://pypi.python.org/pypi/python_secrets

.. image:: https://img.shields.io/travis/davedittrich/python_secrets.svg
        :target: https://travis-ci.org/davedittrich/python_secrets

.. image:: https://readthedocs.org/projects/python_secrets/badge/?version=latest
        :target: https://readthedocs.org/projects/python_secrets/?badge=latest
        :alt: Documentation Status


Python CLI for managing secrets (passwords, API keys, etc)

* Free software: Apache 2.0 License
* Documentation: https://python_secrets.readthedocs.org.

Features
--------

* Uses the `openstack/cliff`_ command line framework.

* Supports a "drop-in" model for defining variables to more easily support
  different use cases and combinations of secrets in a modular manner.

* Support multiple simultaneous sets of secrets for flexibility and
  scalability in multi-environment deployments.

* Produces a single master file for use by Ansible commands (e.g.
  ``ansible-playbook playbook.yml -e @secrets.yml``)

* Define variable names and associate types (e.g., ``password``, ``uuid4``,
  ``consul_key``).

* Allow manual entry of values, or automatic generation according to type.

* Generate unique values for variables, or use a single value per
  type to simplify use of secrets in access control of services
  while supporting a "break-glass" process to quickly regenerate
  secrets when needed.

* List the groups of variables (and how many in each group).

* Show the variables and their unredacted values (or redacted them
  to maintain secrecy during demonstrations or in documentation).

* Output the variables and values in multiple different formats (CSV,
  JSON, YAML) for use in shell scripts, etc. using ``cliff`` features.

.. _openstack/cliff: https://github.com/openstack/cliff

Usage
-----

Getting help
~~~~~~~~~~~~

To get help information on command arguments and options, use
``--help``:

.. code-block:: none


$ python_secrets --help
usage: python_secrets [--version] [-v | -q] [--log-file LOG_FILE] [-h]
                      [--debug] [-e <environment>] [-d <secrets-directory>]
                      [-s <secrets-file>]

Python secrets management app

optional arguments:
  --version             show program's version number and exit
  -v, --verbose         Increase verbosity of output. Can be repeated.
  -q, --quiet           Suppress output except warnings and errors.
  --log-file LOG_FILE   Specify a file to log output. Disabled by default.
  -h, --help            Show help message and exit.
  --debug               Show tracebacks on errors.
  -e <environment>, --environment <environment>
                        Deployment environment selector (Env: D2_ENVIRONMENT;
                        default: None)
  -d <secrets-directory>, --secrets-dir <secrets-directory>
                        Root directory for holding secrets (Env:
                        D2_SECRETS_DIR; default: .)
  -s <secrets-file>, --secrets-file <secrets-file>
                        Secrets file (default: secrets.yml)

Commands:
  complete       print bash completion command (cliff)
  groups         Show a list of secrets groups.
  help           print detailed help for another command (cliff)
  secrets        List the contents of the secrets file
  secrets generate  Generate values for secrets
  secrets set    Set values manually for secrets

..

Directories and files
~~~~~~~~~~~~~~~~~~~~~

By default, ``python_secrets`` looks in the current working directory
for the directory in which variable descriptions are found and to
read/write the file with the secrets (default name, ``security.yml``).
The name of the directory is derived from the name of the secrets file
by stripping off the ``.yml`` extention and adding ``.d`` (following
the Linux drop-in configuration style directories used by programs
like ``rsyslog``, ``dnsmasq``, etc.)

You can define environment variables to point to the root directory
in which a set of different environments can be configured at one
time, to define the current environment, and to change the name
of the secrets file to something else.

.. code-block:: none

    $ env | grep ^D2_
    D2_SECRETS_DIR=/Users/dittrich/.secrets
    D2_ENVIRONMENT=do

..

Each environment is in turn rooted in a directory with the environment's
symbolic name (e.g., ``do`` for DigitalOcean in this example, and ``mantl``
for Cisco's Mantl project.)

.. code-block:: none

    $ tree -L 1 ~/.secrets
    /Users/dittrich/.secrets
    ├── do
    └── mantl

    3 directories, 0 files

..

Each set of secrets for a given service or purpose is described in its own
file.

.. code-block:: none

    .
    ├── secrets.d
    │   ├── ca.yml
    │   ├── consul.yml
    │   ├── jenkins.yml
    │   ├── rabbitmq.yml
    │   ├── trident.yml
    │   ├── vncserver.yml
    │   └── zookeper.yml
    └── secrets.yml

..

A description file looks like this:

.. code-block:: yaml

    ---

    - Variable: jenkins_admin_password
      Type: password

    # vim: ft=ansible :

..

The ``python_secrets`` program uses the `openstack/cliff`_ command line
interface framework, which supports multiple output formats. The default
format the ``table`` format, which makes for nice clean output. (Other
formats will be described later.)

The groups can be listed using the ``groups`` command:

.. code-block:: none

    $ python_secrets groups
    +-----------+-------+
    | Group     | Items |
    +-----------+-------+
    | ca        |     1 |
    | consul    |     1 |
    | jenkins   |     1 |
    | rabbitmq  |     2 |
    | trident   |     2 |
    | vncserver |     1 |
    | zookeper  |     1 |
    +-----------+-------+

..

Generating and Setting variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secrets are generated using the ``secrets generate`` command
and are set manually using the ``secrets set`` command.  To see
all of the secrets, just use the ``secrets`` command by itself:

.. code-block:: none

    $ python_secrets secrets
    +----------------------------+----------+
    | Variable                   | Value    |
    +----------------------------+----------+
    | trident_db_pass            | REDACTED |
    | ca_rootca_password         | REDACTED |
    | consul_key                 | REDACTED |
    | jenkins_admin_password     | REDACTED |
    | rabbitmq_default_user_pass | REDACTED |
    | rabbitmq_admin_user_pass   | REDACTED |
    | trident_sysadmin_pass      | REDACTED |
    | vncserver_password         | REDACTED |
    | zookeeper_uuid4            | REDACTED |
    +----------------------------+----------+

..

By default, the values of secrets are redacted in ``table`` output.  To show
them in the terminal output, add the ``--no-redact`` flag:

.. code-block:: none

    $ python_secrets secrets --no-redact
    +----------------------------+--------------------------------------+
    | Variable                   | Value                                |
    +----------------------------+--------------------------------------+
    | trident_db_pass            | handheld angrily letdown frisk       |
    | ca_rootca_password         | handheld angrily letdown frisk       |
    | consul_key                 | Q04cbB61lm3Z7H+S4WGL+Q==             |
    | jenkins_admin_password     | handheld angrily letdown frisk       |
    | rabbitmq_default_user_pass | handheld angrily letdown frisk       |
    | rabbitmq_admin_user_pass   | handheld angrily letdown frisk       |
    | trident_sysadmin_pass      | handheld angrily letdown frisk       |
    | vncserver_password         | handheld angrily letdown frisk       |
    | zookeeper_uuid4            | 21516a57-e2d3-4d32-a2cc-a364341d24f7 |
    +----------------------------+--------------------------------------+

..

To regenerate all of the secrets at once, using the same value for each
type of secret to simplify things, use the ``secrets generate`` command:

.. code-block:: none

    $ python_secrets secrets generate
    $ python_secrets secrets --no-redact
    +----------------------------+--------------------------------------+
    | Variable                   | Value                                |
    +----------------------------+--------------------------------------+
    | trident_db_pass            | gargle earlobe eggplant kissable     |
    | ca_rootca_password         | gargle earlobe eggplant kissable     |
    | consul_key                 | zQvSe0kdf0Xarbhb80XULQ==             |
    | jenkins_admin_password     | gargle earlobe eggplant kissable     |
    | rabbitmq_default_user_pass | gargle earlobe eggplant kissable     |
    | rabbitmq_admin_user_pass   | gargle earlobe eggplant kissable     |
    | trident_sysadmin_pass      | gargle earlobe eggplant kissable     |
    | vncserver_password         | gargle earlobe eggplant kissable     |
    | zookeeper_uuid4            | 769a77ad-b06f-4018-857e-23f970c777c2 |
    +----------------------------+--------------------------------------+

..

You can set one or more variables manually using ``secrets set`` and
specifying the variable and value in the form ``variable=value``:

.. code-block:: none

    $ python_secrets secrets set trident_db_pass="rural coffee purple sedan"
    $ python_secrets secrets --no-redact
    +----------------------------+--------------------------------------+
    | Variable                   | Value                                |
    +----------------------------+--------------------------------------+
    | trident_db_pass            | rural coffee purple sedan            |
    | ca_rootca_password         | gargle earlobe eggplant kissable     |
    | consul_key                 | zQvSe0kdf0Xarbhb80XULQ==             |
    | jenkins_admin_password     | gargle earlobe eggplant kissable     |
    | rabbitmq_default_user_pass | gargle earlobe eggplant kissable     |
    | rabbitmq_admin_user_pass   | gargle earlobe eggplant kissable     |
    | trident_sysadmin_pass      | gargle earlobe eggplant kissable     |
    | vncserver_password         | gargle earlobe eggplant kissable     |
    | zookeeper_uuid4            | 769a77ad-b06f-4018-857e-23f970c777c2 |
    +----------------------------+--------------------------------------+

..

Or you can generate one or more variables in a similar manner by adding
them to the command line as arguments to ``secrets generate``:

.. code-block:: none

    $ python_secrets secrets generate rabbitmq_default_user_pass rabbitmq_admin_user_pass
    $ python_secrets secrets --no-redact
    +----------------------------+--------------------------------------+
    | Variable                   | Value                                |
    +----------------------------+--------------------------------------+
    | trident_db_pass            | rural coffee purple sedan            |
    | ca_rootca_password         | gargle earlobe eggplant kissable     |
    | consul_key                 | zQvSe0kdf0Xarbhb80XULQ==             |
    | jenkins_admin_password     | gargle earlobe eggplant kissable     |
    | rabbitmq_default_user_pass | embezzle xerox excess skydiver       |
    | rabbitmq_admin_user_pass   | embezzle xerox excess skydiver       |
    | trident_sysadmin_pass      | gargle earlobe eggplant kissable     |
    | vncserver_password         | gargle earlobe eggplant kissable     |
    | zookeeper_uuid4            | 769a77ad-b06f-4018-857e-23f970c777c2 |
    +----------------------------+--------------------------------------+

..

Outputting structured information for use in other scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `openstack/cliff`_ framework also supports multiple output formats that help
with accessing and using the secrets in applications or service configuration
using Ansible.  For example, CSV output (with header) can be produced like this:

.. code-block:: none

    $ python_secrets secrets -f csv
    "Variable","Value"
    "trident_db_pass","gargle earlobe eggplant kissable"
    "ca_rootca_password","gargle earlobe eggplant kissable"
    "consul_key","zQvSe0kdf0Xarbhb80XULQ=="
    "jenkins_admin_password","gargle earlobe eggplant kissable"
    "rabbitmq_default_user_pass","gargle earlobe eggplant kissable"
    "rabbitmq_admin_user_pass","gargle earlobe eggplant kissable"
    "trident_sysadmin_pass","gargle earlobe eggplant kissable"
    "vncserver_password","gargle earlobe eggplant kissable"
    "zookeeper_uuid4","769a77ad-b06f-4018-857e-23f970c777c2"

..

Or you can produce JSON and have structured data for consumption by
other programs.

.. code-block:: none

    $ python_secrets secrets -f json
    [
      {
        "Variable": "trident_db_pass",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "ca_rootca_password",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "consul_key",
        "Value": "zQvSe0kdf0Xarbhb80XULQ=="
      },
      {
        "Variable": "jenkins_admin_password",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "rabbitmq_default_user_pass",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "rabbitmq_admin_user_pass",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "trident_sysadmin_pass",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "vncserver_password",
        "Value": "gargle earlobe eggplant kissable"
      },
      {
        "Variable": "zookeeper_uuid4",
        "Value": "769a77ad-b06f-4018-857e-23f970c777c2"
      }
    ]

..

The JSON can be manipulated, filtered, and restructured using a program
like ``jq``, for example:

.. code-block:: none

    $ python_secrets secrets -f json | jq -r '.[] | { (.Variable): .Value } '
    {
      "trident_db_pass": "gargle earlobe eggplant kissable"
    }
    {
      "ca_rootca_password": "gargle earlobe eggplant kissable"
    }
    {
      "consul_key": "zQvSe0kdf0Xarbhb80XULQ=="
    }
    {
      "jenkins_admin_password": "gargle earlobe eggplant kissable"
    }
    {
      "rabbitmq_default_user_pass": "gargle earlobe eggplant kissable"
    }
    {
      "rabbitmq_admin_user_pass": "gargle earlobe eggplant kissable"
    }
    {
      "trident_sysadmin_pass": "gargle earlobe eggplant kissable"
    }
    {
      "vncserver_password": "gargle earlobe eggplant kissable"
    }
    {
      "zookeeper_uuid4": "769a77ad-b06f-4018-857e-23f970c777c2"
    }

..

.. code-block:: none

    $ python_secrets secrets -f json | jq -r '.[] | [ (.Variable), .Value ] '
    [
      "trident_db_pass",
      "gargle earlobe eggplant kissable"
    ]
    [
      "ca_rootca_password",
      "gargle earlobe eggplant kissable"
    ]
    [
      "consul_key",
      "zQvSe0kdf0Xarbhb80XULQ=="
    ]
    [
      "jenkins_admin_password",
      "gargle earlobe eggplant kissable"
    ]
    [
      "rabbitmq_default_user_pass",
      "gargle earlobe eggplant kissable"
    ]
    [
      "rabbitmq_admin_user_pass",
      "gargle earlobe eggplant kissable"
    ]
    [
      "trident_sysadmin_pass",
      "gargle earlobe eggplant kissable"
    ]
    [
      "vncserver_password",
      "gargle earlobe eggplant kissable"
    ]
    [
      "zookeeper_uuid4",
      "769a77ad-b06f-4018-857e-23f970c777c2"
    ]

..

.. code-block:: none

    $ python_secrets secrets -f json | jq -r '.[] | [ (.Variable), .Value ] |@sh'
    'trident_db_pass' 'gargle earlobe eggplant kissable'
    'ca_rootca_password' 'gargle earlobe eggplant kissable'
    'consul_key' 'zQvSe0kdf0Xarbhb80XULQ=='
    'jenkins_admin_password' 'gargle earlobe eggplant kissable'
    'rabbitmq_default_user_pass' 'gargle earlobe eggplant kissable'
    'rabbitmq_admin_user_pass' 'gargle earlobe eggplant kissable'
    'trident_sysadmin_pass' 'gargle earlobe eggplant kissable'
    'vncserver_password' 'gargle earlobe eggplant kissable'
    'zookeeper_uuid4' '769a77ad-b06f-4018-857e-23f970c777c2'

..

.. code-block:: none

    $ python_secrets secrets -f json | jq -r '.[] | [ (.Variable), .Value ] |@csv'
    "trident_db_pass","gargle earlobe eggplant kissable"
    "ca_rootca_password","gargle earlobe eggplant kissable"
    "consul_key","zQvSe0kdf0Xarbhb80XULQ=="
    "jenkins_admin_password","gargle earlobe eggplant kissable"
    "rabbitmq_default_user_pass","gargle earlobe eggplant kissable"
    "rabbitmq_admin_user_pass","gargle earlobe eggplant kissable"
    "trident_sysadmin_pass","gargle earlobe eggplant kissable"
    "vncserver_password","gargle earlobe eggplant kissable"
    "zookeeper_uuid4","769a77ad-b06f-4018-857e-23f970c777c2"

..

Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-pypackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
