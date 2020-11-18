# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap


from cliff.command import Command
from configobj import ConfigObj


AWS_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
LOG = logging.getLogger(__name__)


class SetAWSCredentials(Command):
    """Set credentials from saved secrets for use by AWS CLI."""

    # See https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html  # noqa

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-U', '--user',
            action='store',
            dest='user',
            default='default',
            help='IAM User who owns credentials (default: "default")'
        )
        parser.epilog = textwrap.dedent("""
            This command directly manipulates the AWS CLI "credentials" INI-style
            file.  The AWS CLI does not support non-interactive manipulation of
            the credentials file, so this hack is used to do this. Be aware that
            this might cause some problems (though it shouldn't, since the file
            is so simple)::

                [default]
                aws_access_key_id = [ Harm to Ongoing Matter ]
                aws_secret_access_key = [        HOM           ]
            \n
            For simple use cases, you will not need to switch between different
            users.  The default is to use the AWS convention of ``default``
            as seen in the example above.  If you do need to support multiple
            users, the ``--user`` option will allow you to specify the user.

            See also:

              * https://aws.amazon.com/cli/
              * https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html
            \n
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[*] setting AWS CLI IAM user credentials')
        self.app.secrets.requires_environment()
        self.app.secrets.read_secrets_and_descriptions()
        required_vars = ['aws_access_key_id', 'aws_secret_access_key']
        config = ConfigObj(AWS_CONFIG_FILE)
        for v in required_vars:
            try:
                cred = self.app.secrets.get_secret(v)
            except Exception as err:  # noqa
                raise
            config[parsed_args.user][v] = cred
        config.write()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
