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

   When originally written, ``python_secrets`` was the primary command name.
   And the Python ``secrets`` module did not yet exist. The name
   ``python_secrets`` is a little unwieldy to type on the command line, so a
   shorter script name ``psec`` was also included in the original release.  The
   original ``python_secrets`` program name is now deprecated.

   In this documentation and command line help, the program name ``psec`` is
   used. (The PyPi package may be renamed at a later date to avoid confusion
   between the package and the program.)

..

The actions are things like ``list``, ``show``, ``generate``, ``set``, etc.

.. note::

    A proof-of-concept for using the ``python_secrets`` package in an open
    source project to eliminate default passwords and keep secrets out of the
    source code repository directory can be found here:

    https://davedittrich.github.io/goSecure/documentation.html

..

Getting help
------------

To get help information on global command arguments and options, use
the ``help`` command or ``--help`` option flag. The usage documentation
below will detail help output for each command.

.. literalinclude:: psec_help.txt

Formatters
----------

The `cliff`_ Command Line Formulation Framework provides a set of
formatting options that facilitate accessing and using stored secrets
in other applications. Data can be passed directly in a structured
format like CSV, or passed directly to programs like Ansible using
JSON.

.. attention::

    The formatter options are shown in the ``--help`` output for individual
    commands (e.g., ``psec secrets show --help``).  For the purposes of this
    chapter, including the lengthy formatter options on every command would be
    quite repetitive and take up a lot of space.  For this reason, the
    formatter options will be suppressed for commands as documented below.  The
    difference (**WITH** and **WITHOUT** the formatting options) would
    look like this:

    **WITH** formatting options

        .. autoprogram-cliff:: psec
           :command: secrets show

    **WITHOUT** formatting options

        .. autoprogram-cliff:: psec
           :command: secrets show
           :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

..

.. _formatting:

Formatting examples
~~~~~~~~~~~~~~~~~~~

CSV output (with header) can be produced like this:

.. code-block:: console

    $ psec secrets show -f csv --column Variable --column Value
    "Variable","Value"
    "trident_db_pass","gargle earlobe eggplant kissable"
    "ca_rootca_password","gargle earlobe eggplant kissable"
    "consul_key","HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY="
    "jenkins_admin_password","gargle earlobe eggplant kissable"
    "rabbitmq_default_user_pass","gargle earlobe eggplant kissable"
    "rabbitmq_admin_user_pass","gargle earlobe eggplant kissable"
    "trident_sysadmin_pass","gargle earlobe eggplant kissable"
    "vncserver_password","gargle earlobe eggplant kissable"
    "zookeeper_uuid4","769a77ad-b06f-4018-857e-23f970c777c2"

..

Or you can produce JSON and have structured data for consumption by
other programs.

.. code-block:: console

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
        "Value": "HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY="
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

.. code-block:: console

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | { (.Variable): .Value } '
    {
      "trident_db_pass": "gargle earlobe eggplant kissable"
    }
    {
      "ca_rootca_password": "gargle earlobe eggplant kissable"
    }
    {
      "consul_key": "HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY="
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

.. code-block:: console

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
      "HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY="
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

.. code-block:: console

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | [ (.Variable), .Value ] |@sh'
    'trident_db_pass' 'gargle earlobe eggplant kissable'
    'ca_rootca_password' 'gargle earlobe eggplant kissable'
    'consul_key' 'HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY='
    'jenkins_admin_password' 'gargle earlobe eggplant kissable'
    'rabbitmq_default_user_pass' 'gargle earlobe eggplant kissable'
    'rabbitmq_admin_user_pass' 'gargle earlobe eggplant kissable'
    'trident_sysadmin_pass' 'gargle earlobe eggplant kissable'
    'vncserver_password' 'gargle earlobe eggplant kissable'
    'zookeeper_uuid4' '769a77ad-b06f-4018-857e-23f970c777c2'

..

.. code-block:: console

    $ psec secrets show -f json --column Variable --column Value |
    > jq -r '.[] | [ (.Variable), .Value ] |@csv'
    "trident_db_pass","gargle earlobe eggplant kissable"
    "ca_rootca_password","gargle earlobe eggplant kissable"
    "consul_key","HEvUAItLFZ0+GjxfwTxLDKq5Fbt86UtXrInzpf71GGY="
    "jenkins_admin_password","gargle earlobe eggplant kissable"
    "rabbitmq_default_user_pass","gargle earlobe eggplant kissable"
    "rabbitmq_admin_user_pass","gargle earlobe eggplant kissable"
    "trident_sysadmin_pass","gargle earlobe eggplant kissable"
    "vncserver_password","gargle earlobe eggplant kissable"
    "zookeeper_uuid4","769a77ad-b06f-4018-857e-23f970c777c2"

..

Commands
--------

The following is reduced ``--help`` output for each subcommand supported by
``psec``. See :ref:`formatting`, or explicitly request ``--help``
output for the subcommand in question on the command line, to see the
suppressed formatting options.


Environments
~~~~~~~~~~~~

.. autoprogram-cliff:: psec
    :command: environments *
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Groups
~~~~~~

.. autoprogram-cliff:: psec
    :command: groups *
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Init
~~~~

.. autoprogram-cliff:: psec
    :command: init
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Run
~~~

.. autoprogram-cliff:: psec
    :command: run
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Secrets
~~~~~~~

.. autoprogram-cliff:: psec
    :command: secrets *
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

SSH
~~~

.. autoprogram-cliff:: psec
    :command: ssh *
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Template
~~~~~~~~

.. autoprogram-cliff:: psec
    :command: template
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Utils
~~~~~

.. autoprogram-cliff:: psec
    :command: utils *
    :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column


.. _cliff: https://pypi.org/project/cliff/
.. _OpenStackClient: https://docs.openstack.org/python-openstackclient/latest/
.. _Command Structure: https://docs.openstack.org/python-openstackclient/latest/cli/commands.html
