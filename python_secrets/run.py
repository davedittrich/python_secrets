import logging

from cliff.command import Command
from subprocess import call  # nosec

# NOTE: While calling subprocess.call() with shell=True can have security
# implications, the person running this command already has control of her
# account.


class Run(Command):
    """Run a command using exported secrets"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.add_argument('args',
                            nargs='*',
                            help='command arguments (default: "env")',
                            default=['env'])
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('running command')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()

        cmd = " ".join(
            [a for a in parsed_args.args]
        ).encode('unicode-escape').decode()
        return call(cmd, shell=True)  # nosec


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
