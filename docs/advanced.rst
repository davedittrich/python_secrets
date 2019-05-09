.. _section_advanced:

==============
Advanced Usage
==============

Managing SSH public keys
------------------------

There is a fundamental problem with using Secure Shell (SSH) access to remote
systems, which is dealing with validation of previously unseen host public
keys. The vulnerability here, as described by SSH.com, is a `MAN-IN-THE-MIDDLE
ATTACK`_.

This problem is bad enough with manually installed computers, either virtual
machines or bare-metal servers.  In a cloud environment, the problem is
exacerbated because every newly instantiated vitual machine may get its own new
IP address, domain name, public and private key pairs. To retrieve the public
key and/or determine the hashes of the public keys in order to validate them,
you must determine the new IP addresses (or DNS names) of every node in the
stack in order to remotely log into the instances using SSH, which requires
validating the hashes of the SSH public keys... see the problem?

There is a better way, which is to retrieve the public keys and/or fingerprints
using the cloud provider's portal console output feature (or the debug output
of a program like Terraform).  ``psec`` has sub-commands that parse the console
output log to extract the keys and then use Ansible to ensure they are present
in the system's ``known_hosts`` file for all to use immediately. (There is an
inverse command to remove these keys when the instance is going to be destroyed
and its IP address changed and SSH keys never to be seen again).

This asciicast shows all of the steps involved in instantiating a new cloud
instance, extracting and storing its SSH public keys, immediately using SSH
without having to validate the key, removing the key, and destroying the
instance.

.. image:: https://asciinema.org/a/245120.svg
   :target: https://asciinema.org/a/245120?autoplay=1
   :align: center
   :alt: Managing SSH host public keys
   :width: 835px

..

.. _MAN-IN-THE-MIDDLE ATTACK: https://www.ssh.com/attack/man-in-the-middle
