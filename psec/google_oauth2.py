# -*- coding: utf-8 -*-


"""
Class for sending cleartext and encrypted emails (optionally with
attachments) using OAuth2 authenticated Google SMTP services.

Adapted from:

* https://github.com/google/gmail-oauth2-tools/blob/master/python/oauth2.py
* https://developers.google.com/identity/protocols/OAuth2

See also:

* https://github.com/google/gmail-oauth2-tools/wiki/OAuth2DotPyRunThrough
* http://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html
* https://developers.google.com/api-client-library/python/guide/aaa_oauth

There are three tasks that can be accomplished using this class:

1. Generating an OAuth2 token with a limited lifetime and a refresh token
   with an indefinite lifetime to use for login (access_token)
2. Generating a new access token using a refresh token (refresh_token)
3. Generating an OAuth2 string that can be passed to IMAP or SMTP servers
   to authenticate connections. (generate_oauth2_string())

"""  # noqa

# Based on 'oauth2.py' example from Google.
# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This script was modified extensively to conform with PEP 8
# requirements and Python 3 coding style.
# Copyright 2018 David Dittrich <dave.dittrich@gmail.com>

# Parts based on 'cryptoletter.py' by Nex
# https://github.com/botherder/cryptoletter/blob/master/cryptoletter.py
# Copyright (c) 2015, Claudio "nex" Guarnieri
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of cryptoletter nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard imports
import base64
import imaplib
import json
import logging
import smtplib
import urllib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# External imports
import gnupg
import lxml.html  # nosec


class GoogleSMTP(object):
    """
    Google OAuth2 SMTP class.
    """
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        username=None,
        client_id=None,
        client_secret=None,
        refresh_token=None,
        verbose=False,
        gpg_encrypt=False,
    ):
        self.username = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.verbose = verbose
        self.gpg = (
            gnupg.GPG(homedir='~/.gnupg', verbose=self.verbose)
            if gpg_encrypt
            else None
        )
        self.access_token = None
        self.expires_in = 0
        self.GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'
        self.REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
        # TODO(dittrich): Disabled this temporarily
        # if self.refresh_token in [None, '']:
        #     self.refresh_token, self.access_token, self.expires_in = \
        #         self.generate_oauth2_token(
        #             self.client_id,
        #             self.client_secret
        #         )

    def set_client_id(self, client_id=None):
        """
        Store the OAuth 2.0 client ID.
        """
        self.client_id = client_id

    def set_client_secret(self, client_secret=None):
        """
        Store the OAuth 2.0 client secret.
        """
        self.client_secret = client_secret

    def command_to_url(self, command):
        """
        Produce an URL for a given command.
        """
        return '{}/{}'.format(self.GOOGLE_ACCOUNTS_BASE_URL, command)

    def url_escape(self, text):
        """
        Escape characters in the URL to reduce risk.
        """
        return urllib.parse.quote(text, safe='~-._')

    def url_unescape(self, text):
        """
        Return URL to standard form.
        """
        return urllib.parse.unquote(text)

    def url_format_params(self, params):
        """
        Format a parameterized URL.
        """
        param_fragments = []
        for param in sorted(params.items(), key=lambda x: x[0]):
            param_fragments.append('{}={}'.format(
                param[0], self.url_escape(param[1])
            ))
        return '&'.join(param_fragments)

    def generate_permission_url(
        self,
        scope='https://mail.google.com/',
    ):
        """
        Generate an OAuth 2.0 authorization URL following the flow
        described in "OAuth2 for Installed Applications":

        * https://developers.google.com/accounts/docs/OAuth2InstalledApp

        Args:
            client_id: Client ID obtained by registering your app.
            scope: scope for access token, e.g. 'https://mail.google.com'
        Returns:
            A URL that the user should visit in their browser.
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.REDIRECT_URI,
            'scope': scope,
            'response_type': 'code',
        }
        return (
            f"{self.command_to_url('o/oauth2/auth')}"
            "?"
            f"{self.url_format_params(params)}"
        )

    def find_keyid(self, recipient, keyid=None):
        """
        Locate the GPG keyid for encrypting a message to the recipient.

        If a keyid is provided, make sure it matches the recipient and
        return None if it does not. Otherwise, walk through all keys in
        the keyring to find a match. If more than one key is found,
        raise a RuntimeError.
        """
        all_keys = self.gpg.list_keys()
        matching_keys = [
            key['keyid']
            for key in all_keys
            for uids in key['uids']
            if (
                (keyid and keyid == key['keyid'])
                or recipient in uids
            )
        ]
        if len(matching_keys) > 1:
            raise RuntimeError(
                '[-] found multiple keys for recipient: '
                ",".join([matching_keys])
            )
        if len(matching_keys) == 0:
            return None
        return matching_keys[0]

    def authorize_tokens(self, auth_token):
        """
        Return OAuth 2.0 authorization token data following the flow
        described in "OAuth2 for Installed Applications":

        * https://developers.google.com/accounts/docs/OAuth2InstalledApp#handlingtheresponse

        Args:
            client_id: Client ID obtained by registering your app.
            client_secret: Client secret obtained by registering your app.
            authorization_code: code generated by Google Accounts after user grants
                permission.
        Returns:
            The decoded response from the Google Accounts server, as a dict. Expected
            fields include 'access_token', 'expires_in', and 'refresh_token'.
         """  # noqa
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_token,
            'redirect_uri': self.REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        request_url = self.command_to_url('o/oauth2/token')
        # bandit security check for Issue: [B310:blacklist]
        # More Info: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b310-urllib-urlopen  # noqa
        if not request_url.startswith('https:'):
            raise RuntimeError(
                "[-] request_url does not start "
                f"with 'https:' - {request_url}")
        response = urllib.request.urlopen(  # nosec
            request_url,
            urllib.parse.urlencode(params).encode('UTF-8')
        ).read().decode('UTF-8')
        return json.loads(response)

    def generate_refresh_token(self):
        """
        Obtains a new OAuth2 authorization token using a refresh token.

        See:
          https://developers.google.com/accounts/docs/OAuth2InstalledApp#refresh

        Args:
          client_id: Client ID obtained by registering your app.
          client_secret: Client secret obtained by registering your app.
          refresh_token: A previously-obtained refresh token.
        Returns:
          The decoded response from the Google Accounts server, as a dict.
          Expected fields include 'access_token', 'expires_in', and
          'refresh_token'.
        """
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        }
        request_url = self.command_to_url('o/oauth2/token')
        # bandit security check for Issue: [B310:blacklist]
        # More Info: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b310-urllib-urlopen  # noqa
        if not request_url.startswith('https:'):
            raise RuntimeError(
                "[-] request_url does not start "
                f"with 'https:' - {request_url}")
        response = urllib.request.urlopen(  # nosec
            request_url,
            urllib.parse.urlencode(params).encode('UTF-8')
        ).read().decode('UTF-8')
        return json.loads(response)

    def generate_oauth2_string(self, base64_encode=False):
        """
        Generates an IMAP OAuth2 authentication string.

        See https://developers.google.com/google-apps/gmail/oauth2_overview

        Args:
          username: the username (email address) of the account to authenticate
          access_token: An OAuth2 access token.
          base64_encode: Whether to base64-encode the output.

        Returns:
          The SASL argument for the OAuth2 mechanism.
        """
        auth_string = (
            f'user={self.username}\1auth=Bearer {self.access_token}\1\1'
        )
        if base64_encode:
            auth_string = base64.b64encode(
                auth_string.encode('ascii')
            ).decode('ascii')
        return auth_string

    def test_imap(self, auth_string):
        """
        Authenticates to IMAP with the given auth_string.

        Prints a debug trace of the attempted IMAP connection.

        Args:
          user: The Gmail username (full email address)
          auth_string: A valid OAuth2 string, as returned by
              generate_oauth2_string().  Must not be base64-encoded,
              since imaplib does its own base64-encoding.
        """
        self.logger.debug('[+] Testing IMAP connection')
        print()
        server = imaplib.IMAP4_SSL('imap.gmail.com')
        server.debug = 4
        server.authenticate('XOAUTH2', lambda x: auth_string)
        server.select('INBOX')

    def test_smtp(self, auth_string):
        """
        Authenticates to SMTP with the given auth_string.

        Args:
          user: The Gmail username (full email address)
          auth_string: A valid OAuth2 string, not base64-encoded, as
              returned by generate_oauth2_string().
        """
        self.logger.debug('[+] Testing SMTP connection')
        print()
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(True)
        server.ehlo('test')
        server.starttls()
        server.docmd('AUTH', 'XOAUTH2 ' + auth_string)

    def get_refresh_token(self):
        """
        Get the OAuth 2.0 refresh token.
        """
        return self.refresh_token

    def get_authorization(self):
        """
        Get OAuth 2.0 authorization URL.
        """
        scope = "https://mail.google.com/"
        print('[+] Navigate to the following URL to authenticate:',
              self.generate_permission_url(scope))
        # >> Issue: [B322:blacklist] The input method in Python 2 will read
        # from standard input, evaluate and run the resulting string as
        # python source code. This is similar, though in many ways worse,
        # then using eval. On Python 2, use raw_input instead, input is
        # safe in Python 3.
        #    Severity: High   Confidence: High
        #    Location: psec/google_oauth2.py:257
        #    More Info: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b322-input  # noqa
        authorization_code = input('[+] Enter verification code: ')  # nosec
        response = self.authorize_tokens(authorization_code)
        self.refresh_token = response['refresh_token']
        self.access_token = response['access_token']
        self.expires_in = response['expires_in']
        return self.refresh_token, self.access_token, self.expires_in

    def refresh_authorization(self):
        """
        Refresh OAuth 2.0 authorization token data.
        """
        response = self.generate_refresh_token()
        self.access_token = response['access_token']
        self.expires_in = response['expires_in']
        return self.access_token, self.expires_in

    def create_msg(
        self,
        fromaddr,
        toaddr,
        subject,
        text_message=None,
        html_message=None,
        addendum=None,
        encrypt_msg=False,
    ):
        """
        Create email message, optionally GPG encrypted.

        Args:
          fromaddr: Email ``From:`` address.
          toaddr: Email ``To:`` address.
          subject: Email ``Subject:`` string.
          text_message: Text for body of email message.
          html_message: Alternative HTML version of body.
          addendum: Signature or other description of the source of the email
              to be appended to the end of the message following ``----``.
          html_message: Alternative HTML version of body.

        If no alternative HTML is included with a text message body, one will
        be generated.

        If the class was initialized with ``gpg_encrypt=True``, the text body
        will be encrypted with GPG before sending using the key associated with
        the recipient. If no key is found, or the encryption fails for some
        other reason, a ``RuntimeError`` exception is raised.
        """
        if text_message is not None and addendum is not None:
            text_message += f"\n----\n{addendum}"
        if self.gpg is not None:
            keyid = self.find_keyid(toaddr)
            if not keyid:
                raise RuntimeError(f"[-] no GPG key found for {toaddr}")
            encrypted_data = self.gpg.encrypt(text_message, keyid)
            if not encrypted_data.ok:
                raise RuntimeError(
                    f"[-] GPG encryption failed: {encrypted_data.stderr}")
            text_body = str(encrypted_data)
        else:
            text_body = text_message
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg.preamble = 'This is a multi-part message in MIME format.'
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        part_text = MIMEText(
            lxml.html.fromstring(text_body).text_content().encode('utf-8'),
            'plain',
            _charset='utf-8',
        )
        if html_message is not None:
            part_html = MIMEText(html_message)
        else:
            part_html = MIMEText(
                text_body.encode('utf-8'),
                'html',
                _charset='utf-8',
            )
        msg_alternative.attach(part_text)
        msg_alternative.attach(part_html)
        return msg

    def send_mail(
        self,
        fromaddr,
        toaddr,
        msg,
    ):
        """
        Send email message.

        Args:
          fromaddr: Email ``From:`` address.
          toaddr: Email ``To:`` address.
          msg: Already fully-populated ``Message`` object.
        """
        self.access_token, self.expires_in = self.refresh_authorization()
        auth_string = self.generate_oauth2_string(base64_encode=True)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo(self.client_id)
        server.starttls()
        server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
        server.sendmail(fromaddr, toaddr, msg.as_string())
        server.quit()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
