============
Installation
============

Install ``psec`` using the ``pip`` module of Python 3.6 (or greater):

.. code-block:: console

   $ python3 -V
   $ Python 3.6.6
   $ python3 -m pip install python_secrets

..

.. image:: https://asciinema.org/a/201502.png
   :target: https://asciinema.org/a/201502?autoplay=1
   :align: center
   :alt: Installation of python_secrets
   :width: 835px

..

For best results, use a Python ``virtualenv`` to avoid problems due to
the system Python not conforming to the version dependency. Even better,
use `pipsi`_ to install ``psec`` as a stand-alone command in its own
wrapped ``virtualenv`` to avoid having to keep it installed and
updated in multiple ``virtualenv``s.

.. _pipsi: https://pypi.org/project/pipsi/
