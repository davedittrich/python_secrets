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

* Supports a "drop-in" model for defining variables in a modular manner
  that is used to then construct a single file for use by Ansible or
  other applications. This is something like the `python-update-dotdee`_
  program, but including secret setting and generation as well.

* Like `python-update-dotdee`_, produces a single master file for use
  by Ansible commands (e.g. ``ansible-playbook playbook.yml -e @secrets.yml``)

* Support multiple simultaneous sets of secrets for flexibility and
  scalability in multi-environment deployments and to support
  different use cases and combinations of secrets.

* Define variable names and associate types (e.g., ``password``, ``uuid4``,
  ``consul_key``).

* Allow manual entry of values, or automatic generation of secrets
  according to their type.

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
.. _python-update-dotdee: https://pypi.org/project/update-dotdee/

Usage
-----

Commands (and subcommands) generally follow the model set by the
`OpenStackClient`_ for its `Command Structure`_. The general structure
of a command is:

.. code-block:: none

   $ python_secrets [<global-options>] <object-1> <action> [<object-2>] [<command-arguments>]

..

The actions are things like ``list``, ``show``, ``create``, ``set``, ``delete``, etc.

.. _OpenStackClient: https://docs.openstack.org/python-openstackclient/latest/
.. _Command Structure: https://docs.openstack.org/python-openstackclient/latest/cli/commands.html

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
  groups list    Show a list of secrets groups.
  help           print detailed help for another command (cliff)
  secrets show   List the contents of the secrets file
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

By default, the values of secrets are redacted when output.  To show
the values in clear text in the terminal output, add the ``--no-redact`` flag:

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

    $ python_secrets secrets show --no-redact -f csv
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

    $ python_secrets secrets show --no-redact -f json
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

    $ python_secrets secrets show --no-redact -f json | jq -r '.[] | { (.Variable): .Value } '
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

    $ python_secrets secrets show --no-redact -f json | jq -r '.[] | [ (.Variable), .Value ] '
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

    $ python_secrets secrets show --no-redact -f json | jq -r '.[] | [ (.Variable), .Value ] |@sh'
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

    $ python_secrets secrets show --no-redact -f json | jq -r '.[] | [ (.Variable), .Value ] |@csv'
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

Future Work
-----------

* Add environment variable ``D2_NO_REDACT`` to change default for the
  ``--no-redact`` option.

* Add ``secrets create`` to add new secrets descriptions + secrets.

* Add ``secrets delete`` to delete secrets.

* Add ``groups create``, ``groups delete``, ``groups show`` commands.

* The Mantl project (GitHub `mantl/mantl`) employs a `security-setup`_ script
  that takes care of setting secrets (and non-secret related variables) in a
  monolithic manner.  It has specific command line options, specific secret
  generation functions, and specific data structures for each of the component
  subsystems used by `mantl`_. This method is not modular or extensible, and
  the `security-setup`_ script is not generalized such that it can be used by
  any other project.  These limitations are primary motivators for writing
  ``python_secrets``, which could eventually replace ``security-setup``.

  At this point, the Mantl ``security.yml`` file can be read in and
  values can be manually set, as seen here:

.. _mantl/mantl: https://github.com/mantl/mantl
.. _security-setup: http://docs.mantl.io/en/latest/security/security_setup.html

  .. code-block:: none

      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets show --no-redact -f yaml
      secrets descriptions directory not found
      - Value: admin:password
        Variable: chronos_http_credentials
      - Value: chronos
        Variable: chronos_principal
      - Value: S0JMz5z8oxQGQXMyZjwE0ZCmu4zeJV4oWDUrdc25MBLx
        Variable: chronos_secret
      - Value: 88821cbe-c004-4cff-9f91-2bc36cd347dc
        Variable: consul_acl_agent_token
      - Value: f9acbe14-28d3-4d06-a1c9-c617da5ebb4e
        Variable: consul_acl_mantl_api_token
      - Value: de54ae85-8226-4146-959f-8926b0b8ee55
        Variable: consul_acl_marathon_token
      - Value: dfc9b244-5140-41ad-b93a-ac5c2451fb95
        Variable: consul_acl_master_token
      - Value: e149b50f-cb5c-4efe-be96-26a52efdc715
        Variable: consul_acl_secure_token
      - Value: 719f2328-6446-4647-adf6-310013bac636
        Variable: consul_acl_vault_token
      - Value: Z0niD1jeiTkx7xaoewJm2A==
        Variable: consul_gossip_key
      - Value: true
        Variable: do_chronos_auth
      - Value: true
        Variable: do_chronos_iptables
      - Value: true
        Variable: do_chronos_ssl
      - Value: true
        Variable: do_consul_auth
      - Value: true
        Variable: do_consul_ssl
      - Value: true
        Variable: do_mantl_api_auth
      - Value: true
        Variable: do_mantlui_auth
      - Value: true
        Variable: do_mantlui_ssl
      - Value: true
        Variable: do_marathon_auth
      - Value: true
        Variable: do_marathon_iptables
      - Value: true
        Variable: do_marathon_ssl
      - Value: true
        Variable: do_mesos_auth
      - Value: true
        Variable: do_mesos_follower_auth
      - Value: true
        Variable: do_mesos_framework_auth
      - Value: true
        Variable: do_mesos_iptables
      - Value: true
        Variable: do_mesos_ssl
      - Value: false
        Variable: do_private_docker_registry
      - Value: mantl-api
        Variable: mantl_api_principal
      - Value: Se4R9nRy8WTAgmU9diJyIPwLYsBU+V1yBxTQumiOriK+
        Variable: mantl_api_secret
      - Value: admin:password
        Variable: marathon_http_credentials
      - Value: marathon
        Variable: marathon_principal
      - Value: +Y5bvIsWliFvcWgbXGWa8kwT6Qf3etogQJe+cK+IV2hX
        Variable: marathon_secret
      - Value:
        - principal: marathon
          secret: +Y5bvIsWliFvcWgbXGWa8kwT6Qf3etogQJe+cK+IV2hX
        - principal: chronos
          secret: S0JMz5z8oxQGQXMyZjwE0ZCmu4zeJV4oWDUrdc25MBLx
        - principal: mantl-api
          secret: Se4R9nRy8WTAgmU9diJyIPwLYsBU+V1yBxTQumiOriK+
        Variable: mesos_credentials
      - Value: follower
        Variable: mesos_follower_principal
      - Value: Q53uAa2mNM0UNe2RUjrX6k7QvK6ojjH1gHXYLcm3Lmfr
        Variable: mesos_follower_secret
      - Value: password
        Variable: nginx_admin_password
      - Value: true
        Variable: security_enabled
      - Value: chronos
        Variable: zk_chronos_user
      - Value: JWPO11z4lU5qeilZ
        Variable: zk_chronos_user_secret
      - Value: hsr+R6YQBAOXoY84a8ne8bU0opg=
        Variable: zk_chronos_user_secret_digest
      - Value: marathon
        Variable: zk_marathon_user
      - Value: UBh77ok2svQAqWox
        Variable: zk_marathon_user_secret
      - Value: mo2mQGXcsc21zB4wYD18jn+Csks=
        Variable: zk_marathon_user_secret_digest
      - Value: mesos
        Variable: zk_mesos_user
      - Value: L3t9FEMsXehqeBvl
        Variable: zk_mesos_user_secret
      - Value: bHYvGteRBxou4jqJ8XWAYmOmzxs=
        Variable: zk_mesos_user_secret_digest
      - Value: super
        Variable: zk_super_user
      - Value: 2DyL/n/GLi3Q0pa75z9OjODGZKC1RCaEiKNV1ZXo1Wpk
        Variable: zk_super_user_secret
      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets show --no-redact -f csv | grep nginx_admin_password
      secrets descriptions directory not found
      "nginx_admin_password","password"
      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets set nginx_admin_password=newpassword
      secrets descriptions directory not found
      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets show --no-redact -f csv | grep nginx_admin_password
      secrets descriptions directory not found
      "nginx_admin_password","newpassword"

  ..

  There are a few things that can be done to use ``python_secrets`` as a replacement
  for the ``security-setup`` script.  These include:

  * Produce secrets descriptions in a ``security.d`` directory.
  * Remove the variables that are not secrets requiring regeneration for rotation
    or "break-glass" procedures (e.g., like ``chronos_principal``, which is a
    userID value, and ``do_mesos_auth``, which is a boolean flag).
  * Break down more complex data structures (specifically, the ``mesos_credentials``
    list of dictionaries with keys ``principal`` and ``secret``). These could
    instead be discrete variables like ``marathon_secret`` (which appears to
    be the secret associated with the invariant "variable" ``marathon_principal``).

  .. note::

     Alternatively, these kind of variables could be supported by defining a type ``invariant``
     or ``string`` and prompting the user to provide a new value (using any current value
     as the default).

  ..

Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-pypackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
