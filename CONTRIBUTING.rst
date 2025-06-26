============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at this repository's GitHub issues page (https://github.com/davedittrich/python_secrets/issues). [1]_

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Output using the ``--debug`` and ``-vvv`` flags.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues [1]_ for bugs. Anything tagged with **bug**
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues [1]_ for features. Anything tagged with **feature**
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

``python_secrets``, like pretty much every open source project, could always use
more user-friendly documentation. That includes this official ``python_secrets``
documentation, docstrings in source code, and around the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/davedittrich/python_secrets/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement the feature.
* Remember that this is a volunteer-driven project, and that contributions
  (i.e., pull requests) *are always welcome*. ;)

Get Started!
------------

Ready to contribute? Here's how to set up `python_secrets` for local development.

#. Fork the `python_secrets` repo on GitHub.

#. Clone your fork locally::

    $ git clone git@github.com:your_name_here/python_secrets.git

#.  Ensure Bats is ready to use for testing. Bats assertion libraries
    are assumed to be installed in Git cloned repositories at the same
    directory level as the ``python_secrets`` repository::

    $ git clone https://github.com/ztombol/bats-support.git
    $ git clone https://github.com/jasonkarns/bats-assert-1.git

#. Install your local copy into a conda environment or virtualenv.
   Using conda (recommended)::

    $ conda create -n python_secrets python=3.10
    $ conda activate python_secrets
    $ cd python_secrets/
    $ make install

   Or using virtualenvwrapper::

    $ mkvirtualenv python_secrets
    $ cd python_secrets/
    $ make install

#. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

#. When you're done making changes, check that your changes pass
   linting, security analysis, and all tests including multiple Python
   versions with ``tox``::

    $ make test

   For individual testing components::

    $ make test-tox          # Run Python unit tests across versions
    $ make test-bats         # Run Bats integration tests
    $ tox run -m static      # Run static analysis (ruff, bandit, docs)
    $ tox -e pep8            # Run ruff linting only
    $ tox -e bandit          # Run security analysis only

#. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

#. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

#. The pull request should include tests.

#. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list of changes in ``HISTORY.rst`` and documentation on use
   in ``README.rst``, ``docs/usage.rst``, and ``parser.epilog`` for CLI
   commands.

#. The pull request should work for Python 3.10, 3.11, and 3.12 as defined
   in ``tox.ini``. Run ``make test`` to ensure compatibility across all
   supported Python versions.

Tips
----

Development and Testing Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project uses **pytest** for unit testing with enhanced type safety and modern Python practices.

To run Python unit tests::

    $ python -m pytest tests/test_secrets.py -v    # Run specific test file
    $ python -m pytest tests/ -k "test_name"       # Run tests matching pattern
    $ python -m pytest tests/ --cov=psec           # Run with coverage

To run Bats integration tests::

    $ make test-bats                               # All Bats tests
    $ bats tests/runtime_10_groups.bats            # Specific test file

Code Quality Standards
~~~~~~~~~~~~~~~~~~~~~~

* **Type Hints**: All new code should include proper type annotations using modern Python typing
* **pytest**: New tests should be written using pytest framework, not unittest
* **Ruff**: Code formatting and linting is handled by Ruff (replaces flake8/black)
* **Bandit**: Security analysis is mandatory for all changes
* **Dataclasses**: Prefer dataclasses over traditional classes where appropriate

Modern Development Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Use ``conda activate psec`` to activate the development environment
2. Run ``make test`` to execute the full test suite
3. Use ``tox run -m static`` for quick linting and security checks
4. Follow the existing code patterns for consistency


.. [1] https://github.com/davedittrich/python_secrets/issues
