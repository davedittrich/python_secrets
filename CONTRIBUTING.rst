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

#. Install your local copy into a virtualenv. Assuming you have
   virtualenvwrapper installed, this is how you set up your fork for
   local development::

    $ mkvirtualenv python_secrets
    $ cd python_secrets/
    $ python setup.py develop

#. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

#. When you're done making changes, check that your changes pass
   ``flake8`` and ``bandit`` (security) tests, including testing
   other Python versions with ``tox``::

    $ make test

   To get ``flake8`` and ``tox``, just ``python -m pip install`` them
   into your virtualenv.

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

#. The pull request should work for the versions of Python defined in ``tox.ini``
   and ``.travis.yml``. Check
   https://travis-ci.org/davedittrich/python_secrets/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of Python unit tests::

    $ python -m unittest tests.test_secrets

To run a subset of Bats tests::

    $ bats tests/secrets.bats


.. [1] https://github.com/davedittrich/python_secrets/issues
