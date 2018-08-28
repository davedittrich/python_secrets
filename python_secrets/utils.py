import ipaddress
import logging
import requests
import subprocess  # nosec
from cliff.command import Command
from six.moves import input

OPENDNS_URL = 'https://diagnostic.opendns.com/myip'
# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.


def get_output(cmd=['echo', 'NO COMMAND SPECIFIED'],
               stderr=subprocess.STDOUT):
    """Use subprocess.check_ouput to run subcommand"""
    output = subprocess.check_output(  # nosec
            cmd, stderr=stderr
        ).decode('UTF-8').splitlines()
    return output


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None


def redact(string, redact=False):
    return "REDACTED" if redact else string


def require_options(options, *args):
    missing = [arg for arg in args if getattr(options, arg) is None]
    if missing:
        raise RuntimeError('Missing options: %s' % ' '.join(missing))
    return True


def prompt_string(prompt="Enter a value",
                  default=None):
    """Prompt the user for a string and return it"""
    _new = None
    while True:
        try:
            _new = str(input("{}? [{}]: ".format(prompt, str(default))))
            break
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue
        except KeyboardInterrupt:
            break
    return default if _new in [None, ''] else _new


class MyIP(Command):
    """Get current internet routable source address."""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('getting current internet source IP address')
        r = requests.get(OPENDNS_URL, stream=True)
        ip_address = ipaddress.ip_address(r.text)
        print(str(ip_address))


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
