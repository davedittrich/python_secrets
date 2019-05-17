.. :changelog:

History
-------

.. Follow: https://keepachangelog.com/en/1.0.0/
..
.. Guiding Principles
.. ------------------
.. Changelogs are for humans, not machines.
.. There should be an entry for every single version.
.. The same types of changes should be grouped.
.. Versions and sections should be linkable.
.. The latest version comes first.
.. The release date of each version is displayed.
.. Mention whether you follow Semantic Versioning.
..
.. Types of changes
.. ----------------
.. Added for new features.
.. Changed for changes in existing functionality.
.. Deprecated for soon-to-be removed features.
.. Removed for now removed features.
.. Fixed for any bug fixes.
.. Security in case of vulnerabilities.

Unreleased
~~~~~~~~~~

Added
^^^^^

- Ability to create an alias for an existing environment


19.4.5 (2019-05-08)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add command 'ssh config' to manage SSH configuration snippet
  for use by 'update-dotdee' to generate ~/.ssh/config file
- Add command 'ssh known-hosts add' and 'ssh known-hosts remove'
  to manage system known_hosts file(s)

Changed
^^^^^^^

- Generalized exception to fix --version bug
- Clean up temporary docs/psec_help.txt file

19.4.4 (2019-04-21)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Fix Bats dependencies/tests
- Fix broken documentation (wt?)
- Fix messed up release tagging

19.4.0 (2019-04-19)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Python 3.7 coverage for Travis CI

Changed
^^^^^^^

- Complete --help output (epilog text) in all commands
- Install a script 'psec' to complement console_script entry point
- Clarify arguments in --help output

Deprecated
^^^^^^^^^^

- The 'python_secrets' command is now just 'psec'

19.3.1 (2019-04-06)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add ``environments rename`` command
- Add ``utils set-aws-credentials`` command to mirror AWS CLI credentials
- Use ``autoprogram_cliff`` for self-documentation
- Add ``cliff.sphinxext`` for documentation

Changed
^^^^^^^

- Refactored ``SecretsEnvironment()`` so ``autoprogram_cliff`` works

18.11.0 (2018-11-09)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add "--type" option to "secrets describe"
- Improve visibility into default environment
- Add screencasts to documenation
- Add RST checks to ensure PyPi documentation works
- Add feedback about minimum Python version
- Add ``--json`` output to ``environments path``
- Add reference to proof-of-concept using goSecure fork

Changed
^^^^^^^

- The "secrets describe" command now describes variables and types
- Allow ``secrets set`` to set any type (not just ``string``)


18.9.0 (2018-09-27)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Switched to calendar version numbering
- Finish GPG encrypted email delivery of secrets
- ``groups create`` command
- Improve error handling consistency when no environment exists


0.16.0 (2018-09-12)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Use attribute maps instead of lookup loops
- Add Prompt attribute in descriptions for better UX when setting variables
- Note new undefined variables when adding groups or ``environments create --clone-from``
- When exporting vars, also export PYTHON_SECRETS_ENVIRONMENT w/environment name
- Add reference to Python Security coding information
- ``environments tree`` command
- ``environments path`` command with features supporting Ansible Lookup Plugin
- ``secrets get`` command
- ``groups path`` command
- ``environments default`` command

0.14.0 (2018-08-30)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Option to export secrets as environment variables (with optional prefix)
- Can now set secrets (any specified or all undefined) via command line
- ``utils myip`` command returns routable IP address (with CIDR option)
- ``run`` command allows running commands with exported environment variables

Changed
^^^^^^^

- Renamed ``template`` comamnd to ``utils tfoutput``

Removed
^^^^^^^

- Dropped support for Python 3.4, 3.5, since ``secrets`` module only in Python >= 3.6


0.10.0 (2018-08-23)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- New ``string`` type for manually set secrets
- ``secrets path`` command provides path to secrets ``.yml`` file
- ``template`` command (Jinja templating)
- Default environment to basename of cwd
- Clone environment from skeleton directory in repo

0.9.1 (2018-08-19)
~~~~~~~~~~~~~~~~~~

Added
^^^^^

- ``secrets describe`` command
- ``environments create`` command
- ``environments list`` command
- Expand secrets types and generation methods
- Add initial feature for sending secrets via email using Google OAuth2 SMTP

Removed
^^^^^^^

- Drop Python 2.7 support (at least for now...)

Security
^^^^^^^^

- Add ``six`` for securing ``input`` call

0.8.0 (2018-05-11)
~~~~~~~~~~~~~~~~~~

(TBD)

0.4.0 (2018-05-01)
~~~~~~~~~~~~~~~~~~

(TBD)

0.3.6 (2018-04-29)
~~~~~~~~~~~~~~~~~~

(TBD)

0.3.0 (2018-04-27)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.
