.. _changelog:

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

23.4.1 (2023-04-19)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Added `secrets find` command.
- Added support for new variable type `boolean`.

Changed
^^^^^^^

- Updated GitHub Actions workflows (default to Python 3.9.16).
- Drop Python 3.7, 3.8, add Python 3.11 (default to 3.10) for `tox`.
- Fixed downstream dependency and `pip` installation problems.
- Resolved new `pep8` and `bandit` findings.

22.6.1 (2022-06-21)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Added `--ignore-missing` option to continue when settings variables.
- Added 'Operational Security' section to README.

22.6.0 (2022-06-10)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add `about` command to expose selected settings for situational awareness.
- Add `pytest` code coverage reporting.
- Add BATS runtime tests related to changes.

Changed
^^^^^^^

- Fix caching bug with non-unique secret generation.
- Fix bugs with setting/deleting secrets.
- Improve secrets basedir initialization logic.
- Expand use of `pathlib.Path`.
- Improvements to source code, test, and vscode launch configuration quality.


22.5.1 (2022-05-25)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Switch to using factory pattern for secrets generation.
- General code quality and test improvements.
- Improve `secrets get` command logic and help.
- Fix `utils yaml-to-json` subcommand and tests.
- Resolve setuptools warnings.
- Separate utility functions from `utils` subcommands.

Removed
^^^^^^^

- Retire `consul_key` secret type in favor of `token_base64`.
- Retire insecure secrets types (e.g., use of SHA1).

22.5.0 (2022-05-11)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Test support for Python 3.10.
- Add better logging controls.

Changed
^^^^^^^

- Generalize Google OAuth2 email functionality.
- Improve use and testing of exceptions.

22.1.0 (2022-01-22)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add `init` command and `--init` flag to initialize secrets base directory.
- Ensure overridden values via flags are exported to process environment
  for subprocesses to use.
- Add missing tests for features added in a previous release.
- Add and start using application-specific exception classes.

Changed
^^^^^^^

- Move functions and variables to `utils` to improve reuse ability.
- Use `get_` prefix more consistently for getter method/function names.
- Over-ride cliff formatter class globally in app parser setup.
- Use `pathlib.Path` for paths for cleaner code.
- Fix bugs in `environments delete` command.
- Fix bugs in `--from-options` feature of `secrets get` and `secrets set`.
- Improvements to source code, test, and vscode launch configuration quality.

21.11.0 (2021-11-22)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add `Help` attribute to descriptions for URL to more information.

Changed
^^^^^^^

- General code quality, documentation, and testing enhancements
- Move `tmpdir` path creation to `secrets_environment.SecretsEnvironment()`.
- Move `umask()` function and variables to `utils`.

Removed
^^^^^^^

- Drop Python 3.6 support due to it being EOL.

21.9.1 (2021-09-15)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Added `secrets tree` subcommand.

Changed
^^^^^^^

- Fixed bugs with `environments path --tmpdir` subcommand and
  `run` subcommand with `--elapsed` option when no environment exists.
- Changed license file name.
- Improved documentation.

21.9.0 (2021-09-07)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Increased test coverage to address bugs (below) being fixed.

Changed
^^^^^^^

- Fixed bugs in `Makefile` and `tox.ini` file.
- Fixed bug setting undefined variables.
- Switched from `numpy` to Python `secrets` module for random bytes.
- Increased key size from 16 to 32 bits for `consul_key`, `token_hex` and `token_urlsafe`.

21.8.0 (2021-08-12)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Fixed bug in setup.py+setup.cfg

21.7.0 (2021-07-30)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Secrets descriptions for demoing HypriotOS Flash mods Medium article

Changed
^^^^^^^

- Improve `secrets set --from-options`
- General code quality, documentation, and testing enhancements

21.6.0 (2021-06-23)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Ability to set and generate secrets from defaults options
- Ability to create an alias for an existing environment
- Allow retroactive mirroring of new secrets

Changed
^^^^^^^

- Switched from `pbr` to `setuptools_scm` for version numbering
- Switched to more secure random number generation

21.2.0 (20201-02-23)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Improve GitHub Actions workflows
- Overall documentation and code enhancements
- Improve handling of wildcards in options list

Changed
^^^^^^^

- Fix bugs with handling empty lists, cloning environments, BATS tests
- Increase password complexity a bit more
- Fix ReadTheDocs

20.11.0 (2020-11-17)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add `secrets create` and `secrets delete` commands

Changed
^^^^^^^

- Normalize all logger and exception output text
- Refactoring code for better modulatiry
- Normalize `group create` and `group delete` code
- Normalize `secrets show` and `secrets describe` code
- Fix bug that left variables missing after cloning
- Add Python 3.9 to testing matrix
- Switch from .yml to .json format for secrets
- Expand IP address support in `utils` subcommand

20.8.1 (2020-08-11)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Fixes to v20.8.0

20.8.0 (2020-08-11)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add GitHub workflow to publish to test.pypi.org
- Add `secrets backup` and `secrets restore` logic
- Open web browser to documentation for help

Changed
^^^^^^^

- Go back to date-based version numbering
- General CI/CD workflow updates
- Improve directory handling in `environments path`

20.2.15 (2012-02-15)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Added Python 3.8 support to test matrix

Changed
^^^^^^^

- Fix bug in `environments default`
- Put elapsed time (and BELL) on stdout
- Fix bug in `environments tree`
- Allow setting vars using diff names+environment

19.12.0 (2019-12-16)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add and document new `boolean` data type
- Add `groups delete` command


Changed
^^^^^^^

- Improve default environment handling
- Improve tox+BATS testing
- Address security issue per "Your xkcd passwords are pwned" article
- General code quality and test improvements
- Add protection from over-writing existing env vars
- Add `Options` attribute

19.11.1 (2019-11-29)
~~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Enhancements to better support Windows 10
- Allow cloning group descriptions from environment
- Fix tty/no-tty handling with `environments delete`
- Expose terraform command on `-v`
- Validate variable exists in environment
- Fix broken `environments tree` code

19.10.1 (2019-10-20)
~~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Move BATS unit tests into tox testing
- Avoid attempting interactive things when no tty
- Improve file and directory permissions logic

19.10.0 (2019-10-14)
~~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Working SSH key and configuration management
- Use `bullet` for interactive list selection
- Elapsed timer feature
- Parsing of terraform output to extract SSH public keys
- `umask` control for better new file permission settings
- Support configuring terraform `tfstate` backend
- Allow setting secrets by copying from another environment

Changed
^^^^^^^

- Numerous bug fixes
- Refine testing
- Option to only show undefined variables
- Sort environments when listing

19.9.0 (2019-09-05)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add `environments delete` subcommand
- Allow cloning environment from an existing one

Changed
^^^^^^^

19.8.3 (2019-08-28)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- Dynamically get version number
- General testing enhancements
- General code quality enhancements
- Ensure more secure file permissions

19.8.2 (2019-08-23)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

- General code quality enhancements

19.8.0 (2019-08-22)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- IP address determination
- Allow cloning new group in an empty environment
- Make `python -m psec` work
- JSON output method
- Environment aliasing feature

Changed
^^^^^^^

- General code quality and testing enhancements
- Be more explicit about default environment
- Tighten permissions on cloned environments/groups
- Add insecure permissions checking

19.5.1 (2019-05-08)
~~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

Add `HISTORY.rst` file

19.4.5 (2019-05-08)
~~~~~~~~~~~~~~~~~~~

Added
^^^^^

- Add command `ssh config` to manage SSH configuration snippet
  for use by `update-dotdee` to generate ~/.ssh/config file
- Add command `ssh known-hosts add` and `ssh known-hosts remove`
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
