# -*- coding: utf-8 -*-

"""
Send secrets using GPG encrypted email.
"""

import logging

from cliff.command import Command
from psec.google_oauth2 import GoogleSMTP


class SecretsSend(Command):
    """
    Send secrets using GPG encrypted email.

    Recipients for the secrets are specified as ``USERNAME@EMAIL.ADDRESS``
    strings and/or ``VARIABLE`` references.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, app, app_args, cmd_name=None):
        super().__init__(app, app_args, cmd_name=None)
        self.refresh_token = None

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '-T', '--refresh-token',
            action='store_true',
            dest='refresh_token',
            default=False,
            help='Refresh Google API Oauth2 token and exit'
        )
        parser.add_argument(
            '--test-smtp',
            action='store_true',
            dest='test_smtp',
            default=False,
            help='Test Oauth2 SMTP authentication and exit'
        )
        parser.add_argument(
            '-H', '--smtp-host',
            action='store',
            dest='smtp_host',
            default='localhost',
            help='SMTP host'
        )
        parser.add_argument(
            '-U', '--smtp-username',
            action='store',
            dest='smtp_username',
            default=None,
            help='SMTP authentication username'
        )
        parser.add_argument(
            '-F', '--from',
            action='store',
            dest='smtp_sender',
            default='noreply@nowhere',
            help='Sender address'
        )
        parser.add_argument(
            '-S', '--subject',
            action='store',
            dest='smtp_subject',
            default='For Your Information',
            help='Subject line'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        return parser

    def take_action(self, parsed_args):
        se = self.app.secrets
        se.requires_environment()
        se.read_secrets_and_descriptions()
        # Attempt to get refresh token first
        orig_refresh_token = None
        self.refresh_token =\
            se.get_secret(
                'google_oauth_refresh_token',
                allow_none=True
            )
        if parsed_args.refresh_token:
            orig_refresh_token = self.refresh_token
            self.logger.debug('[+] refreshing Google Oauth2 token')
        else:
            self.logger.debug('[+] sending secrets')
        if parsed_args.smtp_username is not None:
            username = parsed_args.smtp_username
        else:
            username = se.get_secret(
                'google_oauth_username')
        googlesmtp = GoogleSMTP(
            username=username,
            client_id=se.get_secret(
                'google_oauth_client_id'),
            client_secret=se.get_secret(
                'google_oauth_client_secret'),
            refresh_token=self.refresh_token
        )
        if parsed_args.refresh_token:
            new_refresh_token = googlesmtp.get_authorization()[0]
            if new_refresh_token != orig_refresh_token:
                se.set_secret(
                    'google_oauth_refresh_token',
                    new_refresh_token
                )
            return None
        elif parsed_args.test_smtp:
            auth_string, expires_in = googlesmtp.refresh_authorization()
            googlesmtp.test_smtp(
                googlesmtp.generate_oauth2_string(
                    base64_encode=True))

        recipients = list()
        variables = list()
        for arg in parsed_args.arg:
            if "@" in arg:
                recipients.append(arg)
            else:
                if se.get_secret(arg):
                    variables.append(arg)
        message = "The following secret{} {} ".format(
            "" if len(variables) == 1 else "s",
            "is" if len(variables) == 1 else "are"
            ) + "being shared with you:\n\n" + \
            "\n".join(
                ["{}='{}'".format(v, se.get_secret(v))
                 for v in variables]
            )
        # https://stackoverflow.com/questions/33170016/how-to-use-django-1-8-5-orm-without-creating-a-django-project/46050808#46050808  # noqa
        for recipient in recipients:
            googlesmtp.send_mail(parsed_args.smtp_sender,
                                 recipient,
                                 parsed_args.smtp_subject,
                                 message)
            self.logger.info("[+] sent encrypted secrets to %s", recipient)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
