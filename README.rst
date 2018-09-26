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

Version: 0.17.1

* Free software: Apache 2.0 License
* Documentation: https://python_secrets.readthedocs.org.

Features
--------

* Uses the `openstack/cliff`_ command line framework.

* Supports a "drop-in" model for defining variables in a modular manner
  (something like the `python-update-dotdee`_ program), supporting simplified
  bulk setting or generating variables as needed.

* Like `python-update-dotdee`_, produces a single master ``.yml`` file for
  use by programs like Ansible (e.g.
  ``ansible-playbook playbook.yml -e @"$(python_secrets secrets path)"``)

* Support multiple simultaneous sets of secrets (environments) for
  flexibility and scalability in multi-environment deployments and to
  support different use cases or different combinations of secrets.

* List the groups of variables (and how many secrets in each group).

* Describe secrets by their variable name, type (e.g., ``password``, ``uuid4``,
  ``random_base64``) and an optional description that will be used
  to prompt for values when setting ``string`` variables.

* Allow manual entry of values, or automatic generation of secrets
  according to their type.

* Manually set ``string`` variables based on the output of simple
  commands. This allows interfacing with external programs for
  obtaining secrets, such as `Vault by Hashicorp`_.

* Generate unique values for variables, or use a single value per
  type to simplify use of secrets in access control of services
  while supporting a "break-glass" process to quickly regenerate
  secrets when needed.

* Show the variables and their unredacted values (or redacted them
  to maintain secrecy during demonstrations or in documentation).

* Export the variables (optionally with a specific prefix string)
  to the environment and run a command that inherits them (e.g.,
  to pass variables to `terraform`_ for provisioning cloud
  instances).

* Output the variables and values in multiple different formats (CSV,
  JSON, YAML) for use in shell scripts, etc. using ``cliff`` features.

* Makes it easy to store temporary files (e.g., the output from
  Jinja template rendering)
  that may contain secrets *outside* of the source repo directory
  in an environment-specific ``tmp/`` directory.

.. _openstack/cliff: https://github.com/openstack/cliff
.. _python-update-dotdee: https://pypi.org/project/update-dotdee/
.. _terraform: https://www.terraform.io/
.. _Vault by Hashicorp: https://www.vaultproject.io/

.. note::

   Due to the use of the Python ``secrets`` module, which was introduced
   in Python 3.6, only Python versions >= 3.6 can be used.

..

Limitations
-----------

* Secrets are stored in *unencrypted* form in the environments
  directories.  Permissions are set to limit access, but this is not an
  "encrypt data data at rest" solution like `Vault by Hashicorp`_.

* Does not handle secure distributed access for users on remote systems. You
  must use something like `Vault by Hashicorp`_ or `libfuse/sshfs`_ for secure
  (realtime) distributed access.

* Does not handle secure distribution of newly generated secrets out
  to distributed systems that need them. You will need to use a program
  like `Ansible`_ and related playbooks for pushing out and changing
  secrets (or for retrieving backups). Look at the `D2 Ansible
  playbooks`_ (https://github.com/davedittrich/ansible-dims-playbooks)
  for example playbooks for doing these tasks.

* Does not clean up the environment-specific ``tmp/`` directories.
  (You need to handle that in code, but at least they are less likely
  to end up in a Git commit.)


.. _libfuse/sshfs: https://github.com/libfuse/sshfs
.. _D2 Ansible Playbooks: https://github.com/davedittrich/ansible-dims-playbooks

Usage
-----

Commands (and subcommands) generally follow the model set by the
`OpenStackClient`_ for its `Command Structure`_. The general structure
of a command is:

.. code-block:: shell

   $ psec [<global-options>] <object-1> <action> [<object-2>] [<command-arguments>]

..

.. note::

   When originally written, ``python_secrets`` was the primary command name. That is
   a little unwieldy to type, so a shorter script name ``psec`` was also included.
   You can use either name. In this ``README.rst`` file, both names may be used
   interchangably (but the shorter name is easier to type).

..

The actions are things like ``list``, ``show``, ``generate``, ``set``, etc.

.. _OpenStackClient: https://docs.openstack.org/python-openstackclient/latest/
.. _Command Structure: https://docs.openstack.org/python-openstackclient/latest/cli/commands.html

Getting help
~~~~~~~~~~~~

To get help information on command arguments and options, use
the ``help`` command or ``--help`` option flag:

.. code-block:: shell

    $ psec help
    usage: psec [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]
                [-d <secrets-basedir>] [-e <environment>] [-s <secrets-file>]
                [-P <prefix>] [-E] [--init]

    Python secrets management app

    optional arguments:
      --version             show program's version number and exit
      -v, --verbose         Increase verbosity of output. Can be repeated.
      -q, --quiet           Suppress output except warnings and errors.
      --log-file LOG_FILE   Specify a file to log output. Disabled by default.
      -h, --help            Show help message and exit.
      --debug               Show tracebacks on errors.
      -d <secrets-basedir>, --secrets-basedir <secrets-basedir>
                            Root directory for holding secrets (Env:
                            D2_SECRETS_BASEDIR; default: /Users/dittrich/.secrets)
      -e <environment>, --environment <environment>
                            Deployment environment selector (Env: D2_ENVIRONMENT;
                            default: python_secrets)
      -s <secrets-file>, --secrets-file <secrets-file>
                            Secrets file (default: secrets.yml)
      -P <prefix>, --env-var-prefix <prefix>
                            Prefix string for environment variables (default:
                            None)
      -E, --export-env-vars
                            Export secrets as environment variables (default:
                            False)
      --init                Initialize directory for holding secrets.

    Commands:
      complete       print bash completion command (cliff)
      environments create  Create environment(s)
      environments default  Manage default environment via file in cwd
      environments list  List the current environments
      environments path  Return path to files and directories for environment
      environments tree  Output tree listing of files/directories in environment
      groups create  Create a secrets descriptions group
      groups list    Show a list of secrets groups.
      groups path    Return path to secrets descriptions (groups) directory
      groups show    Show a list of secrets in a group.
      help           print detailed help for another command (cliff)
      run            Run a command using exported secrets
      secrets describe  Describe supported secret types
      secrets generate  Generate values for secrets
      secrets get    Get value associated with a secret
      secrets path   Return path to secrets file
      secrets send   Send secrets using GPG encrypted email.
      secrets set    Set values manually for secrets
      secrets show   List the contents of the secrets file or definitions
      template       Template file(s)
      utils myip     Get current internet routable source address.
      utils tfoutput  Retrieve current 'terraform output' results.

..

Help is also available for individual commands, showing their unique
command line options and arguments. You can get this command-level help
output by using ``help command`` or ``command --help``, like this:

.. code-block:: shell

    $ psec help utils myip
    usage: psec utils myip [-h] [-C]

    Get current internet routable source address.

    optional arguments:
      -h, --help  show this help message and exit
      -C, --cidr  Express IP address as CIDR block (default: False)

..

.. code-block:: shell

    $ psec template --help
    usage: psec template [-h] [--check-defined] [source] [dest]

    Template file(s)

    positional arguments:
      source           input Jinja2 template source
      dest             templated output destination ('-' for stdout)

    optional arguments:
      -h, --help       show this help message and exit
      --check-defined  Just check for undefined variables

..

Directories and files
~~~~~~~~~~~~~~~~~~~~~

There are three file system concepts that are important to understand
regarding secrets storage:

#. The *root directory for secrets storage*;
#. The *environment* for organizing a set of secrets and
   secret group descriptions;
#. The *secrets* file and *group descriptions*.

Root directory
^^^^^^^^^^^^^^

By default, ``python_secrets`` expects a root directory in the current user's
home directory. Unless you over-ride the name of this directory, it defaults to
``.secrets`` on Linux and ``secrets`` on Windows. The ability to change the
location is supported to allow this directory to be placed on an exported
file share, in a common location for use by a group on a workstation, or
to move the contents to a different partition with more disk space.

The first time you use ``python_secrets``, there will likely be no
directory:

.. code-block:: shell

    $ tree ~/.secrets
    /Users/dittrich/.secrets [error opening dir]

    0 directories, 0 files

..

.. note::

   The root directory will be created automatically for you the first time
   you create an environment.

..

Environments
^^^^^^^^^^^^

Environments are sub-directories within the root secrets directory.  You can
just create the directory structure without any files. You create
one environment per set of unique secrets that you need to manage. This could
be one for open source *Program A*, one for *Program B*, etc., or it could be
one for *development*, one for *testing*, one for *production*, etc. (or any
combination).

Use the command ``environments create`` to create an environment.  Since this
program is designed to support multiple environments, a name for the new
environment is required. The name can be provided explicitly, or it can be
inferred from the base name of the current working directory:

.. code-block:: shell

    $ pwd
    /Users/dittrich/git/python_secrets
    $ python_secrets environments create
    environment directory /Users/dittrich/.secrets/python_secrets created
    $ tree ~/.secrets
    /Users/dittrich/.secrets
    └── python_secrets
        └── secrets.d

    2 directories, 0 files

..

Let's say we want to create empty environments for the three deployments
(*development*, *testing*, and *production*). The names can be assigned
explicitly by (a) giving an argument on the command line, (b) using the ``-e`` or
``--environment`` command line flag, or (c) by setting the environment variable
``D2_ENVIRONMENT``:

.. code-block:: shell

    $ python_secrets environments create development
    environment directory /Users/dittrich/.secrets/development created

    $ python_secrets --environment testing environments create
    environment directory /Users/dittrich/.secrets/testing created

    $ D2_ENVIRONMENT=production python_secrets environments create
    environment directory /Users/dittrich/.secrets/production created

    $ tree ~/.secrets
    /Users/dittrich/.secrets
    ├── development
    │   └── secrets.d
    ├── production
    │   └── secrets.d
    ├── python_secrets
    │   └── secrets.d
    └── testing
        └── secrets.d

    8 directories, 0 files

..

If you want to create more than one environment at once, you will
have to specify all of the names on the command line as arguments:

.. code-block:: shell

    $ python_secrets environments create development testing production
    environment directory /Users/dittrich/.secrets/development created
    environment directory /Users/dittrich/.secrets/testing created
    environment directory /Users/dittrich/.secrets/production created

..

The environment directories are useable for storing *all* secrets and
sensitive files (e.g., backups of certificates, databases, etc.) associated
with an environment.

For convenience, there is a command ``environments tree`` that produces
output similar to the Unix ``tree`` command:

.. code-block:: shell

    $ psec -e d2 environments tree
    /Users/dittrich/.secrets/d2
    ├── backups
    │   ├── black.secretsmgmt.tk
    │   │   ├── letsencrypt_2018-04-06T23:36:58PDT.tgz
    │   │   └── letsencrypt_2018-04-25T16:32:20PDT.tgz
    │   ├── green.secretsmgmt.tk
    │   │   ├── letsencrypt_2018-04-06T23:45:49PDT.tgz
    │   │   └── letsencrypt_2018-04-25T16:32:20PDT.tgz
    │   ├── purple.secretsmgmt.tk
    │   │   ├── letsencrypt_2018-04-25T16:32:20PDT.tgz
    │   │   ├── trident_2018-01-31T23:38:48PST.tar.bz2
    │   │   └── trident_2018-02-04T20:05:33PST.tar.bz2
    │   └── red.secretsmgmt.tk
    │       ├── letsencrypt_2018-04-06T23:45:49PDT.tgz
    │       └── letsencrypt_2018-04-25T16:32:20PDT.tgz
    ├── dittrich.asc
    ├── keys
    │   └── opendkim
    │       └── secretsmgmt.tk
    │           ├── 201801.private
    │           ├── 201801.txt
    │           ├── 201802.private
    │           └── 201802.txt
    ├── secrets.d
    │   ├── ca.yml
    │   ├── consul.yml
    │   ├── jenkins.yml
    │   ├── rabbitmq.yml
    │   ├── trident.yml
    │   ├── vncserver.yml
    │   └── zookeper.yml
    ├── secrets.yml
    └── vault_password.txt

..

To just see the directory structure and not files, add the ``--no-files`` option:

.. code-block:: shell

    $ psec -e d2 environments tree --no-files
    /Users/dittrich/.secrets/d2
    ├── backups
    │   ├── black.secretsmgmt.tk
    │   ├── green.secretsmgmt.tk
    │   ├── purple.secretsmgmt.tk
    │   └── red.secretsmgmt.tk
    ├── keys
    │   └── opendkim
    │       └── secretsmgmt.tk
    └── secrets.d

..

Secrets and group descriptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The environment directories just created are all empty. Secrets are stored in a
YML file (``.yml``) within the environment's directory, and group descriptions
are stored in a drop-in directory with the same base name, but with an
extention of ``.d`` instead of ``.yml`` (following the Linux drop-in
configuration style directories used by programs like ``rsyslog``, ``dnsmasq``,
etc.)

The default secrets file name is ``secrets.yml``, which means the default
descriptions directory would be named ``secrets.d``.

You can define environment variables to point to the root directory
in which a set of different environments can be configured at one
time, to define the current environment, and to change the name
of the secrets file to something else.

.. code-block:: shell

    $ env | grep ^D2_
    D2_SECRETS_DIR=/Users/dittrich/.secrets
    D2_ENVIRONMENT=do

..

Each environment is in turn rooted in a directory with the environment's
symbolic name (e.g., ``do`` for DigitalOcean in this example, and ``goSecure``
for the GitHub `davedittrich/goSecure`_ VPN project.)

.. code-block:: shell

    $ tree -L 1 ~/.secrets
    /Users/dittrich/.secrets
    ├── do
    └── goSecure

    3 directories, 0 files

..

.. _davedittrich/goSecure: https://github.com/davedittrich/goSecure

Each set of secrets for a given service or purpose is described in its own
file.

.. code-block:: shell

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

You can see one of the descriptions files from the template
in this repository using ``cat secrets/secrets.d/myapp.yml``:

.. code-block:: yaml

    ---

    - Variable: myapp_pi_password
      Type: password
      Prompt: 'Password for myapp "pi" user account'
      Export: DEMO_pi_password

    - Variable: myapp_app_password
      Type: password
      Prompt: 'Password for myapp web app'
      Export: DEMO_app_password

    - Variable: myapp_client_psk
      Type: string
      Prompt: 'Pre-shared key for myapp client WiFi AP'
      Export: DEMO_client_ssid

    - Variable: myapp_client_ssid
      Type: string
      Prompt: 'SSID for myapp client WiFi AP'
      Export: DEMO_client_ssid

    # vim: ft=ansible :

..

The ``python_secrets`` program uses the `openstack/cliff`_ command line
interface framework, which supports multiple output formats. The default
format the ``table`` format, which makes for nice clean output. (Other
formats will be described later.)

The groups can be listed using the ``groups list`` command:

.. code-block:: shell

    $ psec groups list
    +---------+-------+
    | Group   | Items |
    +---------+-------+
    | jenkins |     1 |
    | myapp   |     4 |
    | trident |     2 |
    +---------+-------+

..

The variables in one or more groups can be shown with
the ``groups show`` command:

.. code-block:: shell

    $ psec groups show trident myapp
    +---------+-----------------------+
    | Group   | Variable              |
    +---------+-----------------------+
    | trident | trident_sysadmin_pass |
    | trident | trident_db_pass       |
    | myapp   | myapp_pi_password     |
    | myapp   | myapp_app_password    |
    | myapp   | myapp_client_psk      |
    | myapp   | myapp_client_ssid     |
    +---------+-----------------------+

..

When integrating a new open source tool or project, you can create
a new group and clone its secrets descriptions. This does not copy
any values, just the descriptions, allowing the current environment
to manage its own values.

.. code-block:: shell

    $ psec groups create newgroup --clone-from ~/git/goSecure/secrets/secrets.d/gosecure.yml
    created new group "newgroup"
    $ psec groups list
    new password variable "gosecure_pi_password" is not defined
    new password variable "gosecure_app_password" is not defined
    new string variable "gosecure_client_psk" is not defined
    new string variable "gosecure_client_ssid" is not defined
    new string variable "gosecure_vpn_client_id" is not defined
    new token_hex variable "gosecure_vpn_client_psk" is not defined
    new string variable "gosecure_pi_pubkey" is not defined
    new string variable "gosecure_pi_locale" is not defined
    new string variable "gosecure_pi_timezone" is not defined
    new string variable "gosecure_pi_wifi_country" is not defined
    new string variable "gosecure_pi_keyboard_model" is not defined
    new string variable "gosecure_pi_keyboard_layout" is not defined
    +----------+-------+
    | Group    | Items |
    +----------+-------+
    | jenkins  |     1 |
    | myapp    |     4 |
    | newgroup |    12 |
    | trident  |     2 |
    +----------+-------+

..


Showing Secrets
~~~~~~~~~~~~~~~

To examine the secrets, use the ``secrets show`` command:

.. code-block:: shell

    $ psec secrets show
    +------------------------+----------+-------------------+----------+
    | Variable               | Type     | Export            | Value    |
    +------------------------+----------+-------------------+----------+
    | jenkins_admin_password | password | None              | REDACTED |
    | myapp_app_password     | password | DEMO_app_password | REDACTED |
    | myapp_client_psk       | string   | DEMO_client_ssid  | REDACTED |
    | myapp_client_ssid      | string   | DEMO_client_ssid  | REDACTED |
    | myapp_pi_password      | password | DEMO_pi_password  | REDACTED |
    | trident_db_pass        | password | None              | REDACTED |
    | trident_sysadmin_pass  | password | None              | REDACTED |
    +------------------------+----------+-------------------+----------+

..

By default, the values of secrets are redacted when output.  To show
the values in clear text in the terminal output, add the ``--no-redact`` flag:

.. code-block:: shell

    $ psec secrets show --no-redact
    +------------------------+----------+-------------------+------------------------------+
    | Variable               | Type     | Export            | Value                        |
    +------------------------+----------+-------------------+------------------------------+
    | jenkins_admin_password | password | None              | fetch outsider awning maroon |
    | myapp_app_password     | password | DEMO_app_password | fetch outsider awning maroon |
    | myapp_client_psk       | string   | DEMO_client_ssid  | PSK                          |
    | myapp_client_ssid      | string   | DEMO_client_ssid  | SSID                         |
    | myapp_pi_password      | password | DEMO_pi_password  | fetch outsider awning maroon |
    | trident_db_pass        | password | None              | fetch outsider awning maroon |
    | trident_sysadmin_pass  | password | None              | fetch outsider awning maroon |
    +------------------------+----------+-------------------+------------------------------+

..

If you don't care about redaction and want to turn it off and save
the dozen keystrokes it takes to type `` --no-redact``, you can export
the environment variable ``D2_NO_REDACT`` set to (case-insensitive)
"true", "1", or "yes". Anything else leaves the default the same.
We'll do this now for later examples.

.. code-block:: shell

    $ export D2_NO_REDACT=true

..

The default is also to show all secrets. If you only want to process a
subset of secrets, you have two ways to do this.

#. Specify the variables you want to show on the command line as arguments:

   .. code-block:: shell

       $ psec secrets show rabbitmq_default_user_pass rabbitmq_admin_user_pass
       +----------------------------+----------+--------------------------------------+
       | Variable                   | Type     | Value                                |
       +----------------------------+----------+--------------------------------------+
       | rabbitmq_default_user_pass | password | handheld angrily letdown frisk       |
       | rabbitmq_admin_user_pass   | password | handheld angrily letdown frisk       |
       +----------------------------+----------+--------------------------------------+

   ..

#. Use the ``--group`` flag and specify the group(s) you want to show
   as command line arguments:

   .. code-block:: shell

       $ psec secrets show --group jenkins trident
       +----------------------------+----------+--------------------------------------+
       | Variable                   | Type     | Value                                |
       +----------------------------+----------+--------------------------------------+
       | jenkins_admin_password     | password | handheld angrily letdown frisk       |
       | trident_db_pass            | password | handheld angrily letdown frisk       |
       | trident_sysadmin_pass      | password | handheld angrily letdown frisk       |
       +----------------------------+----------+--------------------------------------+

   ..

#. Use ``secrets describe`` to see the supported secret types
   that are available for you to use:

   .. code-block:: shell

       $ psec secrets describe
       +------------------+----------------------------------+
       | Type             | Description                      |
       +------------------+----------------------------------+
       | password         | Simple (xkcd) password string    |
       | string           | Simple string                    |
       | crypt_6          | crypt() SHA512 ("$6$")           |
       | token_hex        | Hexadecimal token                |
       | token_urlsafe    | URL-safe token                   |
       | consul_key       | 16-byte BASE64 token             |
       | sha1_digest      | DIGEST-SHA1 (user:pass) digest   |
       | sha256_digest    | DIGEST-SHA256 (user:pass) digest |
       | zookeeper_digest | DIGEST-SHA1 (user:pass) digest   |
       | uuid4            | UUID4 token                      |
       | random_base64    | Random BASE64 token              |
       +------------------+----------------------------------+

   ..

The type ``string`` is for secrets that are managed by another entity that you
must obtain and use to access some remote service (e.g., the pre-shared key for
someone's WiFi network, or an API key for accessing a cloud service provider's
platform). All other types are structured secret types that you generate for
configuring services.

Generating and Setting variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secrets are generated using the ``secrets generate`` command
and are set manually using the ``secrets set`` command.

.. code-block:: shell

    $ psec help secrets generate
    usage: psec secrets generate [-h] [-U] [args [args ...]]

    Generate values for secrets

    positional arguments:
      args

    optional arguments:
      -h, --help    show this help message and exit
      -U, --unique  Generate unique values for each type of secret (default:
                    False)

    ..

.. code-block:: shell

    $ psec secrets set --help
    usage: psec secrets set [-h] [--undefined] [args [args ...]]

    Set values manually for secrets

    positional arguments:
      args

    optional arguments:
      -h, --help   show this help message and exit
      --undefined  Set values for undefined variables (default: False)

..

To regenerate all of the non-string secrets at once, using the same value for
each type of secret to simplify things, use the ``secrets generate`` command:

.. code-block:: shell

    $ psec secrets generate
    $ psec secrets show --column Variable --column Value
    +----------------------------+--------------------------------------+
    | Variable                   | Value                                |
    +----------------------------+--------------------------------------+
    | trident_db_pass            | gargle earlobe eggplant kissable     |
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

.. code-block:: shell

    $ psec secrets set trident_db_pass="rural coffee purple sedan"
    $ psec secrets show --column Variable --column Value
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

.. code-block:: shell

    $ psec secrets generate rabbitmq_default_user_pass rabbitmq_admin_user_pass
    $ psec secrets show --column Variable --column Value
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


A set of secrets for an open source project can be bootstrapped using the
following steps:

#. Create a template secrets environment directory that contains just
   the secrets definitions. This example uses the template found
   in the `davedittrich/goSecure`_ repository
   (directory https://github.com/davedittrich/goSecure/tree/master/secrets).

#. Use this template to clone a secrets environment, which will initially
   be empty:

   .. code-block:: shell

       $ psec environments create test --clone-from ~/git/goSecure/secrets
       new password variable "gosecure_app_password" is not defined
       new string variable "gosecure_client_ssid" is not defined
       new string variable "gosecure_client_ssid" is not defined
       new string variable "gosecure_client_psk" is not defined
       new password variable "gosecure_pi_password" is not defined
       new string variable "gosecure_pi_pubkey" is not defined
       environment directory /Users/dittrich/.secrets/test created

   ..

   .. note::

      If you ever want to suppress messages about new variables, etc., 
      just add the ``-q`` flag:

      .. code-block:: shell

          $ psec -q environments create test --clone-from ~/git/goSecure/secrets
          $

      ..

   .. code-block:: shell

       $ psec -e test secrets show --no-redact --fit-width
       +-----------------------+----------+-------+
       | Variable              | Type     | Value |
       +-----------------------+----------+-------+
       | gosecure_app_password | password | None  |
       | gosecure_client_ssid  | string   | None  |
       | gosecure_client_psk   | string   | None  |
       | gosecure_pi_password  | password | None  |
       | gosecure_pi_pubkey    | string   | None  |
       +-----------------------+----------+-------+

   ..

#. First, generate all secrets whose type is not ``string``:

   .. code-block:: shell

       $ psec -e test secrets generate
       new password variable "gosecure_app_password" is not defined
       new string variable "gosecure_client_ssid" is not defined
       new string variable "gosecure_client_ssid" is not defined
       new string variable "gosecure_client_psk" is not defined
       new password variable "gosecure_pi_password" is not defined
       new string variable "gosecure_pi_pubkey" is not defined

       $ psec -e test secrets show --no-redact --fit-width
       +-----------------------+----------+------------------------------+
       | Variable              | Type     | Value                        |
       +-----------------------+----------+------------------------------+
       | gosecure_app_password | password | brunt outclass alike turbine |
       | gosecure_client_psk   | string   | None                         |
       | gosecure_client_ssid  | string   | None                         |
       | gosecure_pi_password  | password | brunt outclass alike turbine |
       | gosecure_pi_pubkey    | string   | None                         |
       +-----------------------+----------+------------------------------+

   ..

#. Finally, manually set the remaining ``string`` type variables:

   .. code-block:: shell

       $ psec -e test secrets set --undefined
       new string variable "gosecure_client_psk" is not defined
       new string variable "gosecure_client_ssid" is not defined
       new string variable "gosecure_pi_pubkey" is not defined
       Pre-shared key for goSecure client WiFi AP? [None]: atjhK5AlsQMw3Zh
       SSID for goSecure client WiFi AP? [None]: YourWiFiSSID
       SSH public key for accessing "pi" account? [None]: @~/.ssh/new_rsa.pub

       $ psec -e test secrets show --no-redact --fit-width
       +-----------------------+----------+------------------------------------------------------------------------------------------+
       | Variable              | Type     | Value                                                                                    |
       +-----------------------+----------+------------------------------------------------------------------------------------------+
       | gosecure_app_password | password | brunt outclass alike turbine                                                             |
       | gosecure_client_psk   | string   | atjhK5AlsQMw3Zh
       | gosecure_client_ssid  | string   | YourWiFiSSID                                                                             |
       | gosecure_pi_password  | password | brunt outclass alike turbine                                                             |
       | gosecure_pi_pubkey    | string   | ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+qUIucrPvRkTmY0tgxr9ac/VtBUHhYHfOdDVpU99AcryLMWiU |
       |                       |          | uQ2/NVikfOfPo5mt9YTQyqRbeBzKlNgbHnsxh0AZatjhK5AlsQMw3ZhZUcLYZbt7szuQy8ineN0potlCJoVaMSOb |
       |                       |          | 9htf9gAPvzwxUnHxg35jPCzAXYAi3Erc6y338+CL0XxQvCogXOA+MwH7wZGgdT3WpupLG/7HAr/3KJEQQk1FlS2m |
       |                       |          | Rd+WuewnLbKkqBP21N+48ccq6XhEhAmlzzr9SENw5DMmrvMAYIYkoTwUeD3Qx4YebjFkCxZw+w7AafEFn0Kz6vCX |
       |                       |          | 4mp/6ZF/Ko+o04HM2sVr6wtCu2dB dittrich@localhost                                          |
       +-----------------------+----------+------------------------------------------------------------------------------------------+

   ..

.. note::

   If you don't want to see the warnings about new variables that are not
   defined, simply add the ``-q`` flag.

   .. code-block:: shell

       $ psec -q secrets generate
       $ psec -q secrets set --undefined
       Pre-shared key for goSecure client WiFi AP? [None]:

   ..

..

You are now ready to compile your software, or build your project!

There is also a mechanism to run simple commands (i.e., basic arguments with
no special inline command substitution or variable expansion features of
shells like ``bash``) and use the resulting output as the value.

For this example, let's assume an environment that requires a CIDR
notation address for ingres access control (e.g., when using Amazon
Web Services to allow control of instances from your remote laptop).

.. code-block:: shell

    $ psec -e xgt secrets set aws_cidr_allowed=""
    $ psec -e secrets show --no-redact aws_cidr_allowed
    +------------------+--------+-------+
    | Variable         | Type   | Value |
    +------------------+--------+-------+
    | aws_cidr_allowed | string |       |
    +------------------+--------+-------+

..

The ``python_secrets`` program has a utility feature that will return
the current routable IP source address as an IP address, or using CIDR
notation.  The variable can be set in one of two ways:

#. Via (non-interactive) inline command subtitution from the terminal shell:

   .. code-block:: shell

       $ psec -e xgt secrets set aws_cidr_allowed="$(psec utils myip --cidr)"

   ..

#. Interactively when prompted using simple command line form:

   .. code-block:: shell

       $ psec -e xgt secrets set aws_cidr_allowed
       aws_cidr_allowed? []: !psec utils myip --cidr

   ..


The variable now contains the output of the specified program:

.. code-block:: shell

    $ psec secrets show --no-redact aws_cidr_allowed
    +------------------+--------+------------------+
    | Variable         | Type   | Value            |
    +------------------+--------+------------------+
    | aws_cidr_allowed | string | 93.184.216.34/32 |
    +------------------+--------+------------------+

..

.. note::

    If you work from behind a static NAT firewall, this IP address will
    likely not change very often (if at all). If you are using a mobile device
    that is assigned differing DHCP addresses depending on location, the IP address
    may change fairly regularly and the initial AWS Security Group setting will
    begin to block access to your cloud instances. Programs like ``terraform``
    can refresh their state, allowing you to simply reset the variable used to
    create the Security Group and re-apply the plan to regenerate the AWS
    Security Group and re-enable your remote access.

..

.. _davedittrich/goSecure: https://github.com/davedittrich/goSecure/

Outputting structured information for use in other scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once secrets are created and stored, they will eventually need to be accessed
in order to use them in program execution.  This can be done by passing the
``.yml`` secrets file itself to a program, or by outputting the variables in
other formats like CSV, JSON, or as environment type variables.

Passing the secrets file by path
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One way to do this is to take advantage of command line options like
`Ansible`_'s ``--extra-vars`` and passing it a path to the ``.yml`` secrets
file.  (See `Passing Variables On The Command Line`_). You can do that like
this.

Let's assume we want to use ``consul_key`` variable to configure Consul
using Ansible. Here is the variable as stored:

.. code-block:: shell

    $ psec secrets show consul_key
    +------------+------------+--------------------------+
    | Variable   | Type       | Value                    |
    +------------+------------+--------------------------+
    | consul_key | consul_key | GVLKCRqXqm0rxo0b4/ligQ== |
    +------------+------------+--------------------------+

..

Using Ansible's ``debug`` module, we can verify that this variable is not
set by any previously loaded Ansible inventory:

.. code-block:: shell

    $ ansible -i localhost, -m debug -a 'var=consul_key' localhost
    localhost | SUCCESS => {
        "consul_key": "VARIABLE IS NOT DEFINED!"
    }

..

In order for Ansible to set the ``consul_key`` variable outside of any
pre-defined inventory files, we need to pass a file path to the
``--extra-vars`` option. The path can be obtained using the
``psec secrets path`` command:

.. code-block:: shell

    $ psec secrets path
    /Users/dittrich/.secrets/python_secrets/secrets.yml

..

It is possible to run this command in an in-line command expansion operation in
Bash. Ansible expects the file path passed to ``-extra-vars`` to start with an
``@`` character, so the command line to use would look like this:

.. code-block:: shell

    $ ansible -i localhost, -e @"$(psec secrets path)" -m debug -a 'var=consul_key' localhost
    localhost | SUCCESS => {
        "consul_key": "GVLKCRqXqm0rxo0b4/ligQ=="
    }

..

Ansible now has the value and can use it in templating configuration files, or
so forth.

Other programs like Hashicorp `terraform`_ look for environment variables that
begin with ``TF_VAR_`` and use them to set ``terraform`` variables for use
in modules. To prove we are running in a sub-shell, we will first change the
shell prompt.

.. code-block:: shell

    $ PS1="test> "
    test> psec -e test --export-env-vars --env-var-prefix="TEST_" run bash
    $ env | grep '^TEST_'
    TEST_gosecure_pi_pubkey=ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+qUIucrPvRkTmY0tgxr9ac/VtBUHhYHfOdDVpU99AcryLMWiU [...]
    TEST_gosecure_client_psk=atjhK5AlsQMw3Zh
    TEST_gosecure_client_ssid=YourWiFiSSID
    TEST_gosecure_pi_password=brunt outclass alike turbine
    TEST_gosecure_app_password=brunt outclass alike turbine
    $ exit
    test>

..

.. _Ansible: https://docs.ansible.com/
.. _Passing variables on the Command Line: https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#passing-variables-on-the-command-line

Outputting Variables in Other Formats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `openstack/cliff`_ framework also supports multiple output formats that help
with accessing and using the secrets in applications or service configuration
using Ansible.  For example, CSV output (with header) can be produced like this:

.. code-block:: shell

    $ psec secrets show -f csv --column Variable --column Value
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

.. code-block:: shell

    $ psec secrets show -f json --column Variable --column Value
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

.. code-block:: shell

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | { (.Variable): .Value } '
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

.. code-block:: shell

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | [ (.Variable), .Value ] '
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

.. code-block:: shell

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | [ (.Variable), .Value ] |@sh'
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

.. code-block:: shell

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | [ (.Variable), .Value ] |@csv'
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

Python Security
---------------

Last, but certainly not least, take the time to read up on `Python Security`_
and understand the types and sources of security vulnerabilities related to
Python programs. Keep these ideas in mind when using and/or modifying this
program.

.. _Python Security: https://python-security.readthedocs.io/index.html


Future Work
-----------

* Increase test coverage (test driven development is a good thing)

* Add ``secrets create`` to add new secrets descriptions + secrets.

* Add ``secrets delete`` to delete secrets.

* Add ``secrets backup`` and ``secrets restore`` for demo, debugging, experimentation.

* Add ``groups create`` and ``groups delete`` commands.

* The Mantl project (GitHub `mantl/mantl`_) employs a `security-setup`_ script
  that takes care of setting secrets (and non-secret related variables) in a
  monolithic manner.  It has specific command line options, specific secret
  generation functions, and specific data structures for each of the component
  subsystems used by `mantl/mantl`_. This method is not modular or extensible, and
  the `security-setup`_ script is not generalized such that it can be used by
  any other project.  These limitations are primary motivators for writing
  ``python_secrets``, which could eventually replace ``security-setup``.

  At this point, the Mantl ``security.yml`` file can be read in and
  values can be manually set, as seen here:

.. _mantl/mantl: https://github.com/mantl/mantl
.. _security-setup: http://docs.mantl.io/en/latest/security/security_setup.html

  .. code-block:: shell

      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets show -f yaml
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
      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets show -f csv | grep nginx_admin_password
      secrets descriptions directory not found
      "nginx_admin_password","password"
      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets set nginx_admin_password=newpassword
      secrets descriptions directory not found
      $ python_secrets -d ~/git/mantl --secrets-file security.yml secrets show -f csv | grep nginx_admin_password
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

