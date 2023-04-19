=====================
psec (python_secrets)
=====================

.. image:: https://img.shields.io/pypi/v/python_secrets.svg
        :target: https://pypi.python.org/pypi/python_secrets

.. image:: https://img.shields.io/travis/davedittrich/python_secrets.svg
        :target: https://travis-ci.org/davedittrich/python_secrets

.. image:: https://readthedocs.org/projects/python-secrets/badge/?version=latest
        :target: https://python-secrets.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Python command line app for managing groups of secrets (passwords, API keys, etc) and
other project variables. Reduces security risks from things like weak default passwords,
secrets stored in files in the source code repository directory.

Version: 23.4.1

* Free software: `Apache 2.0 License <https://www.apache.org/licenses/LICENSE-2.0>`_
* Documentation: https://python_secrets.readthedocs.org.

Features
--------

* Uses the `openstack/cliff`_ command line framework for a robust and
  full-featured CLI. It is easy to add new commands and features!

* Supports a "drop-in" model for defining variables in a modular manner
  (something like the `python-update-dotdee`_ program), supporting simplified
  bulk setting or generating values of variables as needed.

* Like `python-update-dotdee`_, `psec` produces a single master
  ``.json`` file to hold variables defined by the drop-in group
  description files. That means you can use that file directly
  to set variables to be used from within other programs like
  Ansible (e.g.  ``ansible-playbook playbook.yml -e @"$(psec secrets path)"``)

* Support multiple simultaneous sets of secrets (environments) for
  flexibility and scalability in multi-environment deployments and to
  support different use cases or different combinations of secrets.

* Supports changing the storage location of secrets and variables to
  allow them to be stored on secure mobile media (such as self-encrypting
  external SSD or Flash drives) or encrypted disk images mounted at
  run-time to ensure the confidentiality of data at rest.

* List the groups of variables (and how many secrets in each group).

* Describe secrets by their variable name and type (e.g., ``password``,
  ``uuid4``, ``random_base64``). You can also include a descriptive
  string to prompt the user for a value, a list of options to choose
  from (or ``*`` for "any value the user enters"), and a list of
  environment variables to export for other programs to use at
  run time.

* Allows manual entry of values, setting non-secret variables from
  a default value, or automatic generation of secrets according to
  their type.

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

* Send secrets to other users on demand using GPG encrypted email to
  protect the secrets while in transit and while at rest in users'
  email inboxes.

* Makes it easy to store temporary files (e.g., the output from
  Jinja template rendering)
  that may contain secrets *outside* of the source repo directory
  in an environment-specific ``tmp/`` directory.

.. note::

   Due to the use of the Python ``secrets`` module, which was introduced
   in Python 3.6, only Python versions >= 3.6 can be used.

..

.. _limitations:

Limitations
-----------

* Secrets are stored in *unencrypted* form in the environments
  directories.  Permissions are set to limit access, but this is not an
  "encrypt data at rest" solution like `Vault by Hashicorp`_.

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

Usage Concepts
--------------

There is a separate **Usage** chapter with individual command documentation.
The remainder of this section covers higher level usage concepts necessary to
best use the ``python_secrets`` package in your open source software project.


Directories and files
~~~~~~~~~~~~~~~~~~~~~

There are three file system concepts that are important to understand
regarding secrets storage:

#. The root *secrets base directory* for secrets storage;
#. The *environment* for organizing a set of secrets and
   secret group descriptions;
#. The *secrets* file and *group descriptions*.


.. image:: https://asciinema.org/a/201503.png
   :target: https://asciinema.org/a/201503?autoplay=1
   :align: center
   :alt: Environments
   :width: 835px

..


Secrets Base Directory
^^^^^^^^^^^^^^^^^^^^^^

``psec`` expects to store all of files in a directory tree known as a
*secrets base directory*. Originally, this was intended to be located in the
current user's home directory. Unless you over-ride the name of this directory,
it defaults to ``.secrets`` on Linux and ``secrets`` on Windows.

The ability to locate this directory in a different file system path is
supported by command line options and an environment variable so you can store
files on an exported file share, in a common location for use by a group on a
workstation, or to move the contents to an encrypted disk or a different
partition with more disk space.

The first time you use ever use ``psec``, there will likely be no
directory:

.. code-block:: console

    $ tree ~/.secrets
    /Users/dittrich/.secrets [error opening dir]

    0 directories, 0 files

..

.. note::

   The secrets base directory may be created automatically for you the
   first time you create an environment.  For more information, see
   ``psec init --help``.

..

Environments
^^^^^^^^^^^^

Environments are sub-directories within the root secrets directory.  You can
just create the directory structure without any files. You create
one environment per set of unique secrets that you need to manage. This could
be one for open source *Program A*, one for *Program B*, etc., or it could be
one for *development*, one for *testing*, one for *production*, etc. (or any
combination).

.. image:: https://asciinema.org/a/201505.png
   :target: https://asciinema.org/a/201505?autoplay=1
   :align: center
   :alt: Groups, secrets, generating and setting
   :width: 835px

..

The command ``environments create`` creates an environment.  Since this
program is designed to support multiple environments, a name for the new
environment is required.  The name of the environment can be provided
explicitly, or it can be inferred from the base name of the current working
directory:

.. code-block:: console

    $ pwd
    /Users/dittrich/git/python_secrets
    $ psec environments create
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

.. code-block:: console

    $ psec environments create development
    environment directory /Users/dittrich/.secrets/development created

    $ psec --environment testing environments create
    environment directory /Users/dittrich/.secrets/testing created

    $ D2_ENVIRONMENT=production psec environments create
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

.. code-block:: console

    $ psec environments create development testing production
    environment directory /Users/dittrich/.secrets/development created
    environment directory /Users/dittrich/.secrets/testing created
    environment directory /Users/dittrich/.secrets/production created

..

If you are using one source repository for building multiple deployments, of
course you can't rely on the basename of the directory for all deployments. The
default environment can be set, shown, or unset, using the ``environments
default`` command.

.. code-block:: console

    $ psec environments default --help
    usage: psec environments default [-h] [--unset-default] [environment]

    Manage default environment via file in cwd

    positional arguments:
      environment

    optional arguments:
      -h, --help       show this help message and exit
      --unset-default  Unset localized environment default

..

If no default is explicitly set, the default that would be
applied is returned:

.. code-block:: console

    $ cd ~/git/python_secrets
    $ psec environments default
    default environment is "python_secrets"

..

You can get a list of all available environments at any time,
including which one would be the default used by sub-commands:

.. code-block:: console

    $ psec environments list
    +-------------+---------+
    | Environment | Default |
    +-------------+---------+
    | development | No      |
    | testing     | No      |
    | production  | No      |
    +-------------+---------+

..

The following shows setting and unsetting the default:

.. code-block:: console

    $ psec environments default testing
    default environment set to "testing"
    $ psec environments default
    testing
    $ psec environments list
    +-------------+---------+
    | Environment | Default |
    +-------------+---------+
    | development | No      |
    | testing     | Yes     |
    | production  | No      |
    +-------------+---------+
    $ psec environments default --unset-default
    default environment unset

..

The environment directories are useable for storing *all* secrets and
sensitive files (e.g., backups of certificates, databases, etc.) associated
with an environment.

For convenience, there is a command ``environments tree`` that produces
output similar to the Unix ``tree`` command:

.. code-block:: console

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
    │   ├── ca.json
    │   ├── consul.json
    │   ├── jenkins.json
    │   ├── rabbitmq.json
    │   ├── trident.json
    │   ├── vncserver.json
    │   └── zookeper.json
    ├── secrets.json
    └── vault_password.txt

..

To just see the directory structure and not files, add the ``--no-files`` option:

.. code-block:: console

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
JSON file (``.json``) within the environment's directory, and group descriptions
are stored in a drop-in directory with the same base name, but with an
extention of ``.d`` instead of ``.json`` (following the Linux drop-in
configuration style directories used by programs like ``rsyslog``, ``dnsmasq``,
etc.)

The default secrets file name is ``secrets.json``, which means the default
descriptions directory would be named ``secrets.d``.

You can define environment variables to point to the secrets base directory
in which a set of different environments can be configured at one
time, to define the current environment, and to change the name
of the secrets file to something else.

.. code-block:: console

    $ env | grep ^D2_
    D2_SECRETS_BASEDIR=/Users/dittrich/.secrets
    D2_ENVIRONMENT=do

..

Each environment is in turn rooted in a directory with the environment's
symbolic name (e.g., ``do`` for DigitalOcean in this example, and ``goSecure``
for the GitHub `davedittrich/goSecure`_ VPN project.)

.. code-block:: console

    $ tree -L 1 ~/.secrets
    /Users/dittrich/.secrets
    ├── do
    └── goSecure

    3 directories, 0 files

..


Each set of secrets for a given service or purpose is described in its own
file.

.. code-block:: console

    .
    ├── secrets.d
    │   ├── ca.json
    │   ├── consul.json
    │   ├── jenkins.json
    │   ├── rabbitmq.json
    │   ├── trident.json
    │   ├── vncserver.json
    │   └── zookeper.json
    └── secrets.json

..

You can see one of the descriptions files from the template
in this repository using ``cat tests/secrets.d/myapp.json``:

.. code-block:: json

    [
      {
        "Variable": "myapp_pi_password",
        "Type": "password",
        "Prompt": "Password for myapp 'pi' user account",
        "Export": "DEMO_pi_password"
      },
      {
        "Variable": "myapp_app_password",
        "Type": "password",
        "Prompt": "Password for myapp web app",
        "Export": "DEMO_app_password"
      },
      {
        "Variable": "myapp_client_psk",
        "Type": "string",
        "Prompt": "Pre-shared key for myapp client WiFi AP",
        "Options": "*",
        "Export": "DEMO_client_psk"
      },
      {
        "Variable": "myapp_client_ssid",
        "Type": "string",
        "Prompt": "SSID for myapp client WiFi AP",
        "Options": "myapp_ssid,*",
        "Export": "DEMO_client_ssid"
      },
      {
        "Variable": "myapp_ondemand_wifi",
        "Type": "boolean",
        "Prompt": "'Connect on demand' when connected to wifi",
        "Options": "true,false",
        "Export": "DEMO_ondemand_wifi"
      },
      {
        "Variable": "myapp_optional_setting",
        "Type": "boolean",
        "Prompt": "Optionally do something",
        "Options": "false,true",
        "Export": "DEMO_options_setting"
      }
    ]

..

The ``psec`` program uses the `openstack/cliff`_ command line
interface framework, which supports multiple output formats. The default
format the ``table`` format, which makes for nice clean output. (Other
formats will be described later.)

The groups can be listed using the ``groups list`` command:

.. code-block:: console

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

.. code-block:: console

    $ psec groups show trident myapp
    +---------+-----------------------+
    | Group   | Variable              |
    +---------+-----------------------+
    | trident | trident_sysadmin_pass |
    | trident | trident_db_pass       |
    | myapp   | myapp_app_password    |
    | myapp   | myapp_client_psk      |
    | myapp   | myapp_client_ssid     |
    | myapp   | myapp_ondemand_wifi   |
    | myapp   | myapp_pi_password     |
    +---------+-----------------------+

..

When integrating a new open source tool or project, you can create
a new group and clone its secrets descriptions. This does not copy
any values, just the descriptions, allowing the current environment
to manage its own values.

.. code-block:: console

    $ psec groups create newgroup --clone-from ~/git/goSecure/secrets/secrets.d/gosecure.json
    created new group "newgroup"
    $ psec groups list 2>/dev/null
    +----------+-------+
    | Group    | Items |
    +----------+-------+
    | jenkins  |     1 |
    | myapp    |     5 |
    | newgroup |    12 |
    | trident  |     2 |
    +----------+-------+

..


Showing Secrets
~~~~~~~~~~~~~~~

To examine the secrets, use the ``secrets show`` command:

.. code-block:: console

    $ psec secrets show
    +------------------------+----------+----------+------------------------+
    | Variable               | Type     | Value    | Export                 |
    +------------------------+----------+----------+------------------------+
    | jenkins_admin_password | password | REDACTED | jenkins_admin_password |
    | myapp_app_password     | password | REDACTED | DEMO_app_password      |
    | myapp_client_psk       | string   | REDACTED | DEMO_client_ssid       |
    | myapp_client_ssid      | string   | REDACTED | DEMO_client_ssid       |
    | myapp_ondemand_wifi    | boolean  | REDACTED | DEMO_ondemand_wifi     |
    | myapp_pi_password      | password | REDACTED | DEMO_pi_password       |
    | trident_db_pass        | password | REDACTED | trident_db_pass        |
    | trident_sysadmin_pass  | password | REDACTED | trident_sysadmin_pass  |
    +------------------------+----------+----------+------------------------+

..

By default, the values of secrets are redacted when output.  To show
the values in clear text in the terminal output, add the ``--no-redact`` flag:

.. code-block:: console

    $ psec secrets show --no-redact
    +------------------------+----------+------------------------------+------------------------+
    | Variable               | Type     | Value                        | Export                 |
    +------------------------+----------+------------------------------+------------------------+
    | jenkins_admin_password | password | fetch.outsider.awning.maroon | jenkins_admin_password |
    | myapp_app_password     | password | fetch.outsider.awning.maroon | DEMO_app_password      |
    | myapp_client_psk       | string   | PSK                          | DEMO_client_psk        |
    | myapp_client_ssid      | string   | SSID                         | DEMO_client_ssid       |
    | myapp_ondemand_wifi    | boolean  | true                         | DEMO_ondemand_wifi     |
    | myapp_pi_password      | password | fetch.outsider.awning.maroon | DEMO_pi_password       |
    | trident_db_pass        | password | fetch.outsider.awning.maroon | trident_db_pass        |
    | trident_sysadmin_pass  | password | fetch.outsider.awning.maroon | trident_sysadmin_pass  |
    +------------------------+----------+------------------------------+------------------------+

..

If you don't care about redaction and want to turn it off and save
the dozen keystrokes it takes to type `` --no-redact``, you can export
the environment variable ``D2_NO_REDACT`` set to (case-insensitive)
"true", "1", or "yes". Anything else leaves the default the same.
We'll do this now for later examples.

.. code-block:: console

    $ export D2_NO_REDACT=true

..

The default is also to show all secrets. If you only want to process a
subset of secrets, you have two ways to do this.

#. Specify the variables you want to show on the command line as arguments:

   .. code-block:: console

       $ psec secrets show rabbitmq_default_user_pass rabbitmq_admin_user_pass
       +----------------------------+----------+--------------------------------------+
       | Variable                   | Type     | Value                                |
       +----------------------------+----------+--------------------------------------+
       | rabbitmq_default_user_pass | password | handheld.angrily.letdown.frisk       |
       | rabbitmq_admin_user_pass   | password | handheld.angrily.letdown.frisk       |
       +----------------------------+----------+--------------------------------------+

   ..

#. Use the ``--group`` flag and specify the group(s) you want to show
   as command line arguments:

   .. code-block:: console

       $ psec secrets show --group jenkins trident
       +----------------------------+----------+--------------------------------------+
       | Variable                   | Type     | Value                                |
       +----------------------------+----------+--------------------------------------+
       | jenkins_admin_password     | password | handheld.angrily.letdown.frisk       |
       | trident_db_pass            | password | handheld.angrily.letdown.frisk       |
       | trident_sysadmin_pass      | password | handheld.angrily.letdown.frisk       |
       +----------------------------+----------+--------------------------------------+

   ..


Describing Secrets and Secret Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To describe the secrets in the select environment, use the
``secrets describe`` command:

.. code-block:: console

    $ psec secrets describe
    +----------------------------+----------+--------------------------------------------+
    | Variable                   | Type     | Prompt                                     |
    +----------------------------+----------+--------------------------------------------+
    | google_oauth_client_id     | string   | Google OAuth2 client id                    |
    | google_oauth_client_secret | string   | Google OAuth2 client secret                |
    | google_oauth_refresh_token | string   | Google OAuth2 refresh token                |
    | google_oauth_username      | None     | google_oauth_username                      |
    | jenkins_admin_password     | password | Password for Jenkins "admin" account       |
    | myapp_app_password         | password | Password for myapp web app                 |
    | myapp_client_psk           | string   | Pre-shared key for myapp client WiFi AP    |
    | myapp_client_ssid          | string   | SSID for myapp client WiFi AP              |
    | myapp_ondemand_wifi        | boolean  | "Connect on demand" when connected to wifi |
    | myapp_pi_password          | password | Password for myapp "pi" user account       |
    | trident_db_pass            | password | Password for Trident postgres database     |
    | trident_sysadmin_pass      | password | Password for Trident sysadmin account      |
    +----------------------------+----------+--------------------------------------------+
    $ psec secrets describe --group trident
    +-----------------------+----------+----------------------------------------+
    | Variable              | Type     | Prompt                                 |
    +-----------------------+----------+----------------------------------------+
    | trident_db_pass       | password | Password for Trident postgres database |
    | trident_sysadmin_pass | password | Password for Trident sysadmin account  |
    +-----------------------+----------+----------------------------------------+

..

To get a description of the available secret types, add the ``--types`` flag.

.. code-block:: console

    $ psec secrets describe --types
    +------------------+----------------------------------+
    | Type             | Description                      |
    +------------------+----------------------------------+
    | password         | Simple (xkcd) password string    |
    | string           | Simple string                    |
    | boolean          | Boolean ("true"/"false")         |
    | crypt_6          | crypt() SHA512 ("$6$")           |
    | token_hex        | Hexadecimal token                |
    | token_urlsafe    | URL-safe token                   |
    | sha256_digest    | DIGEST-SHA256 (user:pass) digest |
    | uuid4            | UUID4 token                      |
    | random_base64    | Random BASE64 token              |
    +------------------+----------------------------------+

..

.. note::

    The type ``string`` is for secrets that are managed by another entity that you
    must obtain and use to access some remote service (e.g., the pre-shared key for
    someone's WiFi network, or an API key for accessing a cloud service provider's
    platform). All other types are structured secret types that you generate for
    configuring services.

..

Generating and Setting variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secrets are generated using the ``secrets generate`` command
and are set manually using the ``secrets set`` command.

.. code-block:: console

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

.. code-block:: console

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

.. code-block:: console

    $ psec secrets generate
    $ psec secrets show --column Variable --column Value
    +----------------------------+----------------------------------------------+
    | Variable                   | Value                                        |
    +----------------------------+----------------------------------------------+
    | trident_db_pass            | gargle.earlobe.eggplant.kissable             |
    | ca_rootca_password         | gargle.earlobe.eggplant.kissable             |
    | consul_key                 | HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY= |
    | jenkins_admin_password     | gargle.earlobe.eggplant.kissable             |
    | rabbitmq_default_user_pass | gargle.earlobe.eggplant.kissable             |
    | rabbitmq_admin_user_pass   | gargle.earlobe.eggplant.kissable             |
    | trident_sysadmin_pass      | gargle.earlobe.eggplant.kissable             |
    | vncserver_password         | gargle.earlobe.eggplant.kissable             |
    | zookeeper_uuid4            | 769a77ad-b06f-4018-857e-23f970c777c2         |
    +----------------------------+----------------------------------------------+

..

You can set one or more variables manually using ``secrets set`` and
specifying the variable and value in the form ``variable=value``:

.. code-block:: console

    $ psec secrets set trident_db_pass="rural coffee purple sedan"
    $ psec secrets show --column Variable --column Value
    +----------------------------+----------------------------------------------+
    | Variable                   | Value                                        |
    +----------------------------+----------------------------------------------+
    | trident_db_pass            | rural coffee purple sedan                    |
    | ca_rootca_password         | gargle.earlobe.eggplant.kissable             |
    | consul_key                 | HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY= |
    | jenkins_admin_password     | gargle.earlobe.eggplant.kissable             |
    | rabbitmq_default_user_pass | gargle.earlobe.eggplant.kissable             |
    | rabbitmq_admin_user_pass   | gargle.earlobe.eggplant.kissable             |
    | trident_sysadmin_pass      | gargle.earlobe.eggplant.kissable             |
    | vncserver_password         | gargle.earlobe.eggplant.kissable             |
    | zookeeper_uuid4            | 769a77ad-b06f-4018-857e-23f970c777c2         |
    +----------------------------+----------------------------------------------+

..

.. caution::

   Note in the example above that the command argument is
   ``trident_db_pass="rural coffee purple sedan"`` and not
   ``trident_db_pass='rural coffee purple sedan'``.
   When using the ``variable=value`` form of the ``secrets set``
   command with a value that contains spaces, you **must** quote the value with
   the double-quote character (``"``) as opposed to the single-quote
   (apostrophe, or ``'``) character. The Bash shell (and possibly other
   shells) will not properly parse the command line and the resulting
   ``sys.argv`` argument vector will be incorrectly set as seen here:

   .. code-block:: console

       _sys.argv[1:] = {list} <class 'list'>: ['--debug', 'secrets', 'set', 'trident_db_password=rural coffee purple sedan']
        0 = {str} '--debug'
        1 = {str} 'secrets'
        2 = {str} 'set'
        3 = {str} 'trident_db_password=rural coffee purple sedan'
        __len__ = {int} 4


       _sys.argv[1:] = {list} <class 'list'>: ['--debug', 'secrets', 'set', "trident_db_password='rural", 'coffee', 'purple', "sedan'"]
        0 = {str} '--debug'
        1 = {str} 'secrets'
        2 = {str} 'set'
        3 = {str} 'trident_db_password=\\'rural'
        4 = {str} 'coffee'
        5 = {str} 'purple'
        6 = {str} 'sedan\\''
        __len__ = {int} 7

..

Or you can generate one or more variables in a similar manner by adding
them to the command line as arguments to ``secrets generate``:

.. code-block:: console

    $ psec secrets generate rabbitmq_default_user_pass rabbitmq_admin_user_pass
    $ psec secrets show --column Variable --column Value
    +----------------------------+----------------------------------------------+
    | Variable                   | Value                                        |
    +----------------------------+----------------------------------------------+
    | trident_db_pass            | rural.coffee.purple.sedan                    |
    | ca_rootca_password         | gargle.earlobe.eggplant.kissable             |
    | consul_key                 | HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY= |
    | jenkins_admin_password     | gargle.earlobe.eggplant.kissable             |
    | rabbitmq_default_user_pass | embezzle.xerox.excess.skydiver               |
    | rabbitmq_admin_user_pass   | embezzle.xerox.excess.skydiver               |
    | trident_sysadmin_pass      | gargle.earlobe.eggplant.kissable             |
    | vncserver_password         | gargle.earlobe.eggplant.kissable             |
    | zookeeper_uuid4            | 769a77ad-b06f-4018-857e-23f970c777c2         |
    +----------------------------+----------------------------------------------+

..


A set of secrets for an open source project can be bootstrapped using the
following steps:

#. Create a template secrets environment directory that contains just
   the secrets definitions. This example uses the template found
   in the `davedittrich/goSecure`_ repository
   (directory https://github.com/davedittrich/goSecure/tree/master/secrets).

#. Use this template to clone a secrets environment, which will initially
   be empty:

   .. code-block:: console

       $ psec environments create test --clone-from ~/git/goSecure/secrets
       new password variable "gosecure_app_password" is unset
       new string variable "gosecure_client_ssid" is unset
       new string variable "gosecure_client_ssid" is unset
       new string variable "gosecure_client_psk" is unset
       new password variable "gosecure_pi_password" is unset
       new string variable "gosecure_pi_pubkey" is unset
       environment directory /Users/dittrich/.secrets/test created

   ..

   .. note::

      The warnings about undefined new variables are presented on the standard
      error file handle (a.k.a., ``&2``). You get rid of them on the console by
      redirecting ``stderr`` to ``/dev/null`` or a file:

      .. code-block:: console

          $ psec environments create test --clone-from ~/git/goSecure/secrets 2>/dev/null
          environment directory /Users/dittrich/.secrets/test created

      ..

   .. code-block:: console

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

   .. code-block:: console

       $ psec -e test secrets generate
       new password variable "gosecure_app_password" is unset
       new string variable "gosecure_client_ssid" is unset
       new string variable "gosecure_client_ssid" is unset
       new string variable "gosecure_client_psk" is unset
       new password variable "gosecure_pi_password" is unset
       new string variable "gosecure_pi_pubkey" is unset

       $ psec -e test secrets show --no-redact --fit-width
       +-----------------------+----------+------------------------------+
       | Variable              | Type     | Value                        |
       +-----------------------+----------+------------------------------+
       | gosecure_app_password | password | brunt.outclass.alike.turbine |
       | gosecure_client_psk   | string   | None                         |
       | gosecure_client_ssid  | string   | None                         |
       | gosecure_pi_password  | password | brunt.outclass.alike.turbine |
       | gosecure_pi_pubkey    | string   | None                         |
       +-----------------------+----------+------------------------------+

   ..

#. Finally, manually set the remaining ``string`` type variables:

   .. code-block:: console

       $ psec -e test secrets set --undefined
       new string variable "gosecure_client_psk" is unset
       new string variable "gosecure_client_ssid" is unset
       new string variable "gosecure_pi_pubkey" is unset
       Pre-shared key for goSecure client WiFi AP? [None]: atjhK5AlsQMw3Zh
       SSID for goSecure client WiFi AP? [None]: YourWiFiSSID
       SSH public key for accessing "pi" account? [None]: @~/.ssh/new_rsa.pub

       $ psec -e test secrets show --no-redact --fit-width
       +-----------------------+----------+------------------------------------------------------------------------------------------+
       | Variable              | Type     | Value                                                                                    |
       +-----------------------+----------+------------------------------------------------------------------------------------------+
       | gosecure_app_password | password | brunt.outclass.alike.turbine                                                             |
       | gosecure_client_psk   | string   | atjhK5AlsQMw3Zh
       | gosecure_client_ssid  | string   | YourWiFiSSID                                                                             |
       | gosecure_pi_password  | password | brunt.outclass.alike.turbine                                                             |
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

   .. code-block:: console

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

.. code-block:: console

    $ psec -e xgt secrets set aws_cidr_allowed=""
    $ psec -e secrets show --no-redact aws_cidr_allowed
    +------------------+--------+-------+
    | Variable         | Type   | Value |
    +------------------+--------+-------+
    | aws_cidr_allowed | string |       |
    +------------------+--------+-------+

..

The ``psec`` program has a utility feature that will return
the current routable IP source address as an IP address, or using CIDR
notation.  The variable can be set in one of two ways:

#. Via (non-interactive) inline command subtitution from the terminal shell:

   .. code-block:: console

       $ psec -e xgt secrets set aws_cidr_allowed="$(psec utils myip --cidr)"

   ..

#. Interactively when prompted using simple command line form:

   .. code-block:: console

       $ psec -e xgt secrets set aws_cidr_allowed
       aws_cidr_allowed? []: !psec utils myip --cidr

   ..


The variable now contains the output of the specified program:

.. code-block:: console

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


Sharing secrets
~~~~~~~~~~~~~~~

The ``psec`` program has a mechanism for sharing secrets with
others using GPG encrypted email messages for securing secrets in transit
and at rest in users' inboxes. Email is sent using Google's OAuth2
authenticated SMTP services.

.. note::

   The Electronic Frontier Foundation (EFF) has a `Surveillance Self-Defense
   Guide`_ that includes guides on `How to Use PGP for Linux`_ and other operating
   systems. Follow their instructions if you are new to PGP/GPG.

..

The command is ``secrets send``.

.. code-block:: console

    $ psec secrets send --help
    usage: psec secrets send [-h] [-T] [--test-smtp] [-H SMTP_HOST]
                             [-U SMTP_USERNAME] [-F SMTP_SENDER] [-S SMTP_SUBJECT]
                             [args [args ...]]

    Send secrets using GPG encrypted email. Arguments are USERNAME@EMAIL.ADDRESS
    and/or VARIABLE references.

    positional arguments:
      args

    optional arguments:
      -h, --help            show this help message and exit
      -T, --refresh-token   Refresh Google API Oauth2 token and exit (default:
                            False)
      --test-smtp           Test Oauth2 SMTP authentication and exit (default:
                            False)
      -H SMTP_HOST, --smtp-host SMTP_HOST
                            SMTP host (default: localhost)
      -U SMTP_USERNAME, --smtp-username SMTP_USERNAME
                            SMTP authentication username (default: None)
      -F SMTP_SENDER, --from SMTP_SENDER
                            Sender address (default: 'noreply@nowhere')
      -S SMTP_SUBJECT, --subject SMTP_SUBJECT
                            Subject line (default: 'For Your Information')

..

Any arguments (``args``) that contain the ``@`` symbol are assumed to be email
addresses while the rest are assumed to be the names of secrets variables
to be sent.

All recipients must have GPG public keys in your keyring.  An exception is thrown
if no GPG key is associated with the recipient(s) email addresses.

.. code-block:: console

    $ psec secrets send dittrich@u.washington.edu myapp_app_password
    Setting homedir to '/Users/dittrich/.gnupg'

    Initialised settings:
    binary: /usr/local/bin/gpg
    binary version: 1.4.11\ncfg:pubkey:1;2;3;16;17\ncfg:cipher:2;3;4;7;8;9;10;11;12;13\ncfg:ciphername:3DES;CAST5;BLOWFISH;AES;AES192;AES256;TWOFISH;CAMELLIA128;CAMELLIA192;CAMELLIA256\ncfg:digest:1;2;3;8;9;10;11\ncfg:digestname:MD5;SHA1;RIPEMD160;SHA256;SHA384;SHA512;SHA224\ncfg:compress:0;1;2;3\n'
    homedir: /Users/dittrich/.gnupg
    ignore_homedir_permissions: False
    keyring: /Users/dittrich/.gnupg/pubring.gpg
    secring: /Users/dittrich/.gnupg/secring.gpg
    default_preference_list: SHA512 SHA384 SHA256 AES256 CAMELLIA256 TWOFISH AES192 ZLIB ZIP Uncompressed
    keyserver: hkp://wwwkeys.pgp.net
    options: None
    verbose: False
    use_agent: False

    Creating the trustdb is only available with GnuPG>=2.x
    sent encrypted secrets to dittrich@u.washington.edu

..

Use ``-q`` to produce no extraneous output.

.. code-block:: console

    $ psec -q secrets send dittrich@u.washington.edu myapp_app_password

..

The resulting email looks like this:

.. code-block:: console

    Message-ID: <5bac64ce.1c69fb81.b136e.45ae@mx.google.com>
    Date: Wed, 26 Sep 2018 22:04:14 -0700 (PDT)
    From: dave.dittrich@gmail.com
    X-Google-Original-From: noreply@nowhere
    Content-Type: multipart/related; boundary="===============6413073026511107073=="
    MIME-Version: 1.0
    Subject: For Your Information
    To: dittrich@u.washington.edu

    This is a multi-part message in MIME format.
    --===============6413073026511107073==
    Content-Type: multipart/alternative; boundary="===============2830935289665347054=="
    MIME-Version: 1.0

    --===============2830935289665347054==
    Content-Type: text/plain; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: base64

    LS0tLS1CRUdJTiBQR1AgTUVTU0FHRS0tLS0tCgpoUUlXQStSZlhnK3dLTGJlRUFnZlFNcjZYb0lT
    cS9BaTlMbEVpZTFTejd5ckEzUmN4SWdjb01XTUNSM3JBaXBHCjF0TTJoZkpxRGJZOThSOEVST01F
    aVltSzR2aVJ4ZjgrSU54NU54SUJPbFh1T1JQTy82NElUKzdrVSt5aDZGV00KNU1MK0Jkb21sQzNF
    eC9pd3hwbTJ1R2FPczFpcU9DaDIxbTd5RnJWYkNVSW5NN1ZiMTEwck41aXNOZ3BFdndrQgpaZHhp
    alJqazdtYVl1eFNkc2c3Y2RVQ29uSmdBR214QU0vZkFzOTREcHNrYkwzMFpqZE1iRHlMbUk4NWp2
    QU45CjU3KzAxLzM1MEMyN1hrbEUxdEZudWNlRkRqZ04zeEd4K2Zud0pqdkFpNUpaVHltanRkQi9r
    dUZUMlJTTmJJTlAKMWRZdHp4WGxNeVd0SVphNDVYcHdNenZ1TkFTbEJtbENjQXk4YlluSEJmeFRy
    SGdJSUlCMlZNY1N6dmdjR3BtVApkYzZqaDVOeEV1bWljOWdXMmplSnFqRHRtdW9Ib3dxZldZb2xX
    bGlXUTMrNDNzeVkrdHFlMGgvWEwzS2ZxSTMrClZzWWdyQmpGd0hnem1INEthMWxucXdUZkMzZTJ3
    cUI4Uk5hcllqcXAzbHFQOVBhMHdzSVVWMHVYN2dhL01kVWcKdHNRSktPWWJRTnlXVTFLZEZWNHl4
    Ynp1TWVlQ3ltMmxMbXJwVks5T3hCV04vbCtXMjRsWmhkck9TcGFJQnpNdgpnc1p3VWVuVzBXR054
    bklwUGhoSWRuVE40ZlNscE5JVDhMcmJYeUhoY2ZVS2lsUDNpeEVPRS9Lc25QUFJNTURFCk9SY0xT
    Z3FMMTB4b0toMnNzZTNxNG5RaHZkZW5IVVVxVjJ0WW1UVmRCNVl3cTN1MFdtY3BGSGU2NnBZeTBB
    VSsKdzRjb2JVM2crQWtJMHBNQnllRzZYaWV4VzF1UzRLVVVnaFlhWVlYQ2dnazJZNEpZT05QSDJJ
    NlIydmxuNjFsVApZdm1tR0NNamw3cC9pTnE2RWJpbndoMnNsbkpLMHd3S1BIbVBPUjJvRjdWREN0
    dE9idHA0cEZUWTNHalByc0dRCkNDT3dYR2hCSFVQRnY2c3R4NEdtUi9GUWpBRWxxaEpjQWtTbDFz
    WWhsUFRhSmEyVGgyNG81L1lPUmxRaHhhRUgKUEFrNFgzcGVCMk9UVjRNR2RCOD0KPTc0aXEKLS0t
    LS1FTkQgUEdQIE1FU1NBR0UtLS0tLQo=

    --===============2830935289665347054==
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: base64

    VGhlIGZvbGxvd2luZyBzZWNyZXQgaXMgYmVpbmcgc2hhcmVkIHdpdGggeW91OgoKbXlhcHBfYXBw
    X3Bhc3N3b3JkPWJydW50IG91dGNsYXNzIGFsaWtlIHR1cmJpbmU=

    --===============2830935289665347054==--

    --===============6413073026511107073==--

..

Decrypted, it looks like this:

.. code-block:: console

    Date: Wed, 26 Sep 2018 22:04:14 -0700 (PDT)
    From: dave.dittrich@gmail.com
    Subject: For Your Information
    To: dittrich@u.washington.edu

    The following secret is being shared with you:

    myapp_app_password=brunt.outclass.alike.turbine

    --
    Sent using psec version 23.4.1
    https://pypi.org/project/python-secrets/
    https://github.com/davedittrich/python_secrets

..

A group of secrets required for Google's `OAuth 2.0 Mechanism`_  is provided
and must be set according to Google's instructions. See also:

+ https://github.com/google/gmail-oauth2-tools/wiki/OAuth2DotPyRunThrough

+ http://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html

+ https://developers.google.com/api-client-library/python/guide/aaa_oauth

+ https://github.com/google/gmail-oauth2-tools/blob/master/python/oauth2.py

+ https://developers.google.com/identity/protocols/OAuth2


.. code-block:: console

    $ psec groups show oauth
    +-------+----------------------------+
    | Group | Variable                   |
    +-------+----------------------------+
    | oauth | google_oauth_client_id     |
    | oauth | google_oauth_client_secret |
    | oauth | google_oauth_refresh_token |
    +-------+----------------------------+

..


Processing templates
~~~~~~~~~~~~~~~~~~~~

.. image:: https://asciinema.org/a/201507.png
   :target: https://asciinema.org/a/201507?autoplay=1
   :align: center
   :alt: Rendering templates outside the source repo directory
   :width: 835px

..


Outputting structured information for use in other scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once secrets are created and stored, they will eventually need to be accessed
in order to use them in program execution.  This can be done by passing the
``.json`` secrets file itself to a program, or by outputting the variables in
other formats like CSV, JSON, or as environment type variables.

Passing the secrets file by path
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One way to do this is to take advantage of command line options like
`Ansible`_'s ``--extra-vars`` and passing it a path to the ``.json`` secrets
file.  (See `Passing Variables On The Command Line`_). Here is how to do
it.

Let's assume we want to use ``consul_key`` variable to configure Consul
using Ansible. Here is the variable as stored:

.. code-block:: console

    $ psec secrets show consul_key
    +------------+-----------+----------------------------------------------+
    | Variable   | Type      | Value                                        |
    +------------+-----------+----------------------------------------------+
    | consul_key | token_hex | HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY= |
    +------------+-----------+----------------------------------------------+

..

Using Ansible's ``debug`` module, we can verify that this variable is not
set by any previously loaded Ansible inventory:

.. code-block:: console

    $ ansible -i localhost, -m debug -a 'var=consul_key' localhost
    localhost | SUCCESS => {
        "consul_key": "VARIABLE IS NOT DEFINED!"
    }

..

In order for Ansible to set the ``consul_key`` variable outside of any
pre-defined inventory files, we need to pass a file path to the
``--extra-vars`` option. The path can be obtained using the
``psec secrets path`` command:

.. code-block:: console

    $ psec secrets path
    /Users/dittrich/.secrets/python_secrets/secrets.json

..

It is possible to run this command in an in-line command expansion operation in
Bash. Ansible expects the file path passed to ``-extra-vars`` to start with an
``@`` character, so the command line to use would look like this:

.. code-block:: console

    $ ansible -i localhost, -e @"$(psec secrets path)" -m debug -a 'var=consul_key' localhost
    localhost | SUCCESS => {
        "consul_key": "HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY="
    }

..

Ansible now has the value and can use it in templating configuration files, or
so forth.

Other programs like Hashicorp `terraform`_ look for environment variables that
begin with ``TF_VAR_`` and use them to set ``terraform`` variables for use
in modules. To prove we are running in a sub-shell, we will first change the
shell prompt.

.. code-block:: console

    $ PS1="test> "
    test> psec -e test --export-env-vars --env-var-prefix="TEST_" run bash
    $ env | grep '^TEST_'
    TEST_gosecure_pi_pubkey=ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+qUIucrPvRkTmY0tgxr9ac/VtBUHhYHfOdDVpU99AcryLMWiU [...]
    TEST_gosecure_client_psk=atjhK5AlsQMw3Zh
    TEST_gosecure_client_ssid=YourWiFiSSID
    TEST_gosecure_pi_password=brunt.outclass.alike.turbine
    TEST_gosecure_app_password=brunt.outclass.alike.turbine
    $ exit
    test>

..

.. image:: https://asciinema.org/a/201510.png
   :target: https://asciinema.org/a/201510?autoplay=1
   :align: center
   :alt: Exporting secrets via the environment
   :width: 835px

..



Operational Security
----------------------

As noted in the Limitations section above, secrets are stored in plaintext
plaintext form (i.e., they are *not* encrypted) in files. Those files are in
turn stored in a directory in the file system, subject to Linux file
ownership and permission access controls.

The default location for storing these files is in an *environment directory*
in a subdirectory of the user's home directory whose name starts with a period
character (a.k.a., a *dot*).  Files (or directories) whose name starts with a
period are known as *dot files*, or *hidden files* because the `ls` command
does not show it unless you use the `-a` flag.

The secrets environment directories can also be used to store other files
besides secrets. One such use case is storing JSON Web Tokens (JWTs) used as
bearer tokens by protocols like Google's `OAuth 2.0 Mechanism`_ for securing
access to web services and APIs. While this improves security in terms of
remote access, is not not without its own risks (including the JWT file being
stored in the file system for an indefinite period of time).

* `JSON Web Tokens (JWT) are Dangerous for User Sessions—Here’s a
  Solution`_, by Raja Rao, June 24, 2021

* `Stop Using JSON Web Tokens For Authentication. Use Stateful Sessions
  Instead`_, by Francisco Sainz, April 4, 2022

* `What’s the Secure Way to Store JWT?`_, by Yang Liu, July 23, 2020

Besides JWTs, other use cases for storing sensitive files within `psec`
environments include backups of database contents, Let's Encrypt certificates,
SSH keys, or other secrets necessary for ensuring cloud instances can be
destroyed and recreated without losing state or requiring regeneration
(and redistribution or revalidation) of secrets.

The output of `init --help` mentions this risk and offers a way to mitigate
some of the risk by locating the secrets storage base directory within a
directory that is stored on an encrypted USB-connected disk device or encrypted
disk image, or a removable device or remote file system, that is only mounted
when needed and unmounted as soon as possible. This ensures sensitive data that
are not being actively used are left encrypted in storage.  The
`D2_SECRETS_BASEDIR` environment variable or `-d` option allow you to specify
the directory to use.

The `psec` CLI has a secure deletion mechanism that over-writes file contents
prior to deletion, helping to reduce leaving remnants of secrets in unallocated
file system storage, similar to the way the Linux `shred` command works.



Python Script Security
----------------------

Last, but certainly not least, take the time to read up on `Python Security`_
and understand the types and sources of security vulnerabilities related to
Python programs. Keep these ideas in mind when using and/or modifying this
program.

As part of testing, the `Bandit`_ security validation program is used.
(See `Getting started with Bandit`_).

.. _Bandit: https://pypi.org/project/bandit/
.. _Getting started with Bandit: https://developer.rackspace.com/blog/getting-started-with-bandit/

In situations where Bandit warnings can safely be ignored, the ``# nosec``
comment appears on source code lines. Comments as to why these can be
safely ignored are included in the code. (Please feel free to issue pull
requests if you disagree.)

One runtime security mechanism employed by ``psec`` is control of the process'
``umask``. This is important when running programs that create files, which
will inherit their permissions per the process ``umask``. The ``umask`` will be
inherited by every new child process and can be set in the user's ``.bashrc``
(or other shell initialization) file.

The ``psec run`` command can be used to run programs as child processes,
optionally exporting environment variables as well, so controlling the
``umask`` results in improved file permission security regardless of
whether the user knows to set their process ``umask``.

You can see the effect in these two examples.

First, by setting the ``umask`` to ``0`` you see the very permissive file
permissions (as well as getting a warning from ``psec`` about finding a file
with lax permissions):

.. code-block:: console

    $ psec --umask 0o000 run -- dd if=/dev/random count=1 of=$(psec environments path --tmpdir)/foo
    1+0 records in
    1+0 records out
    512 bytes copied, 0.000019 s, 2.7 MB/s
    $ ls -l $(psec environments path --tmpdir)/foo
    [!] file /Users/dittrich/.secrets/python_secrets/tmp/foo is mode 0o100666
    -rw-rw-rw- 1 dittrich staff 512 Sep  8 13:05 /Users/dittrich/.secrets/python_secrets/tmp/foo
    $ rm $(psec environments path --tmpdir)/foo

..

Now when using the default ``--umask`` value, the file permissions are restricted
(and thus no more warning):

.. code-block:: console

    $ psec run -- dd if=/dev/random count=1 of=$(psec environments path --tmpdir)/foo
    1+0 records in
    1+0 records out
    512 bytes copied, 0.000243 s, 2.1 MB/s
    $ ls -l $(psec environments path --tmpdir)/foo
    -rw------- 1 dittrich staff 512 Sep  8 13:04 /Users/dittrich/.secrets/python_secrets/tmp/foo
    $ rm $(psec environments path --tmpdir)/foo

..

Bugs, Enhancements, and Future Work
-----------------------------------

Feature requests (and of course bug reports) are highly encouraged. You can
do that by `opening an issue`_ on GitHub. Better yet, make a `pull
request`_ with your own fix or feature. (Check there to see if one
may already exist.)

If you want to help, there are some things that are on the "to do"
list. These are tracked on this repository's GitHub `Projects`_ page.

General or more elaborate potential enhancements are listed here:

* Increase test coverage (test driven development is a Good Thing(TM))

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

  .. code-block:: console

      $ psec -d ~/git/mantl --secrets-file security.yml secrets show -f yaml
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
      $ psec -d ~/git/mantl --secrets-file security.yml secrets show -f csv | grep nginx_admin_password
      secrets descriptions directory not found
      "nginx_admin_password","password"
      $ psec -d ~/git/mantl --secrets-file security.yml secrets set nginx_admin_password=newpassword
      secrets descriptions directory not found
      $ psec -d ~/git/mantl --secrets-file security.yml secrets show -f csv | grep nginx_admin_password
      secrets descriptions directory not found
      "nginx_admin_password","newpassword"

  ..

  There are a few things that can be done to use ``psec`` as a replacement
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
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-pypackage`_

Development of this program was supported in part under an Open Source
Development Grant from the Comcast Innovation Fund.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _openstack/cliff: https://github.com/openstack/cliff
.. _python-update-dotdee: https://pypi.org/project/update-dotdee/
.. _terraform: https://www.terraform.io/
.. _Vault by Hashicorp: https://www.vaultproject.io/
.. _mantl/mantl: https://github.com/mantl/mantl
.. _security-setup: http://docs.mantl.io/en/latest/security/security_setup.html
.. _Ansible: https://docs.ansible.com/
.. _libfuse/sshfs: https://github.com/libfuse/sshfs
.. _D2 Ansible Playbooks: https://github.com/davedittrich/ansible-dims-playbooks
.. _Passing variables on the Command Line: https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#passing-variables-on-the-command-line
.. _OAuth 2.0 Mechanism: https://developers.google.com/gmail/imap/xoauth2-protocol.
.. _davedittrich/goSecure: https://github.com/davedittrich/goSecure
.. _Surveillance Self-Defense Guide: https://ssd.eff.org/en
.. _opening an issue: https://github.com/davedittrich/python_secrets/issues
.. _pull request: https://github.com/davedittrich/python_secrets/pulls
.. _Projects: https://github.com/davedittrich/python_secrets/projects/1
.. _How to Use PGP for Linux: https://ssd.eff.org/en/module/how-use-pgp-linux
.. _Python Security: https://python-security.readthedocs.io/index.html
.. _JSON Web Tokens (JWT) are Dangerous for User Sessions—Here’s a Solution: https://redis.com/blog/json-web-tokens-jwt-are-dangerous-for-user-sessions/
.. _Stop Using JSON Web Tokens For Authentication. Use Stateful Sessions Instead: https://betterprogramming.pub/stop-using-json-web-tokens-for-authentication-use-stateful-sessions-instead-c0a803931a5d
.. _What’s the Secure Way to Store JWT?: https://medium.com/swlh/whats-the-secure-way-to-store-jwt-dd362f5b7914
