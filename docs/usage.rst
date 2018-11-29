.. _section_usage:

=====
Usage
=====

Commands (and subcommands) generally follow the model set by the
`OpenStackClient`_ for its `Command Structure`_. The general structure
of a command is:

.. code-block:: console

   $ psec [<global-options>] <object-1> <action> [<object-2>] [<command-arguments>]

..

.. note::

   When originally written, ``python_secrets`` was the primary command name. That is
   a little unwieldy to type, so a shorter script name ``psec`` was also included.
   You can use either name. In this ``README.rst`` file, both names may be used
   interchangably (but the shorter name is easier to type).

..

The actions are things like ``list``, ``show``, ``generate``, ``set``, etc.

.. note::

    A proof-of-concept for using ``python_secrets`` in an open source
    project to eliminate default passwords and keep secrets out of the
    source code repository directory can be found here:

    https://davedittrich.github.io/goSecure/documentation.html

..

Getting help
------------

To get help information on global command arguments and options, use
the ``help`` command or ``--help`` option flag. The usage documentation
below will detail help output for each command.

.. code-block:: console

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
      utils set-aws-credentials  Set credentials from saved secrets for use by AWS CLI.
      utils tfoutput  Retrieve current 'terraform output' results.

..

Environments
------------

.. autoprogram-cliff:: python_secrets
   :application: psec
   :command: environments *

Groups
------

.. autoprogram-cliff:: python_secrets
   :application: psec
   :command: groups *

Run
---

.. autoprogram-cliff:: python_secrets
   :application: psec
   :command: run

Secrets
-------

.. autoprogram-cliff:: python_secrets
   :application: psec
   :command: secrets *

Template
--------

.. autoprogram-cliff:: python_secrets
   :application: psec
   :command: template

Utils
-----

.. autoprogram-cliff:: python_secrets
   :application: psec
   :command: utils *


.. _OpenStackClient: https://docs.openstack.org/python-openstackclient/latest/
.. _Command Structure: https://docs.openstack.org/python-openstackclient/latest/cli/commands.html
