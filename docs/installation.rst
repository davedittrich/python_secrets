============
Installation
============

Install ``psec`` using the ``pip`` module of Python 3.6 (or greater):

.. code-block:: console

   $ python -V
   $ Python 3.9.0
   $ python -m pip install python_secrets

..

.. image:: https://asciinema.org/a/201502.png
   :target: https://asciinema.org/a/201502?autoplay=1
   :align: center
   :alt: Installation of python_secrets
   :width: 835px

..

For best results, use a Python ``virtualenv`` to avoid problems due to
the system Python not conforming to the version dependency. User's with
Mac OS X systems and Windows systems may want to use ``miniconda`` to
standardize management of your virtual environments across those two
operating systems as well as Linux.

If you are not doing a lot of Python development and just want to use
``psec`` for managing secrets in your open source projects (or as part
of an open source project that depends on ``psec`` for configuration
files that include secrets) there are some simpler options that
transparently handle the virtual environment creation for you. The
``pipx`` program is easy to install as a PyPI package, or with
Homebrew on the Mac (see https://pipxproject.github.io/pipx/ for
installation instructions).
