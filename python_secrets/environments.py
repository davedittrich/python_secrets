import logging
import os

from cliff.command import Command
from cliff.lister import Lister
from python_secrets.secrets import SecretsEnvironment


class EnvironmentsList(Lister):
    """List the current environments"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsList, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('listing environment(s)')
        columns = (['Environment'])
        basedir = self.app.secrets.root_path()
        data = (
            [e] for e in os.listdir(basedir)
            if os.path.isdir(os.path.join(basedir, e))
        )
        return columns, data


class EnvironmentsCreate(Command):
    """Create environment(s)"""

    LOG = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EnvironmentsCreate, self).get_parser(prog_name)
        parser.add_argument(
            '-C', '--clone-from',
            action='store',
            dest='clone_from',
            default=None,
            help="Environment directory to clone from (default: None)"
        )
        parser.add_argument('args',
                            nargs='*',
                            default=[self.app.options.environment])
        return parser

    def take_action(self, parsed_args):
        self.LOG.debug('creating environment(s)')
        # basedir = self.app.get_secrets_basedir()
        if len(parsed_args.args) == 0:
            parsed_args.args = list(self.app.options.environment)
        for e in parsed_args.args:
            se = SecretsEnvironment(environment=e)
            se.environment_create(source=parsed_args.clone_from)
            self.app.LOG.info('environment directory {} created'.format(
                se.environment_path()))

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
