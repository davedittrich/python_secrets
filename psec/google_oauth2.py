# -*- coding: utf-8 -*-

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


import base64
import imaplib
import json
import gnupg
import lxml.html  # nosec
import smtplib
import textwrap
import urllib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from psec import __version__

"""
https://github.com/google/gmail-oauth2-tools/wiki/OAuth2DotPyRunThrough

http://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html
https://developers.google.com/api-client-library/python/guide/aaa_oauth

Adapted from:
https://github.com/google/gmail-oauth2-tools/blob/master/python/oauth2.py
https://developers.google.com/identity/protocols/OAuth2

1. Generate and authorize an OAuth2 (generate_oauth2_string())
2. Generate a new access token using a refresh token (refresh_token)
3. Generate an OAuth2 string to use for login (access_token)
"""


class GoogleSMTP(object):
    def __init__(self,
                 username=None,
                 client_id=None,
                 client_secret=None,
                 refresh_token=None):

        """Google OAuth2 SMTP object."""

        self.username = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

        self.access_token = None
        self.expires_in = 0

        self.GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'
        self.REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

        self.gpg = gnupg.GPG(homedir='~/.gnupg')

        # TODO(dittrich): Disabled this temporarily
        # if self.refresh_token in [None, '']:
        #     self.refresh_token, self.access_token, self.expires_in = \
        #         self.generate_oauth2_token(self.client_id,
        #                                    self.client_secret)

    def set_client_id(self, client_id=None):
        self.client_id = client_id

    def set_client_secret(self, client_secret=None):
        self.client_secret = client_secret

    def command_to_url(self, command):
        return '{}/{}'.format(self.GOOGLE_ACCOUNTS_BASE_URL, command)

    def url_escape(self, text):
        return urllib.parse.quote(text, safe='~-._')

    def url_unescape(self, text):
        return urllib.parse.unquote(text)

    def url_format_params(self, params):
        param_fragments = []
        for param in sorted(params.items(), key=lambda x: x[0]):
            param_fragments.append('{}={}'.format(
                param[0], self.url_escape(param[1])
            ))
        return '&'.join(param_fragments)

    def generate_permission_url(self,
                                scope='https://mail.google.com/'):
        params = dict()
        params['client_id'] = self.client_id
        params['redirect_uri'] = self.REDIRECT_URI
        params['scope'] = scope
        params['response_type'] = 'code'
        return '{}?{}'.format(self.command_to_url('o/oauth2/auth'),
                              self.url_format_params(params))

    def find_keyid(self, recipient):
        # We need the keyid to encrypt the message to the recipient.
        # Let's walk through all keys in the keyring and find the
        # appropriate one.
        keys = self.gpg.list_keys()
        for key in keys:
            for uid in key['uids']:
                if recipient in uid:
                    return key['keyid']
        return None

    def authorize_tokens(self, auth_token):
        params = dict()
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        params['code'] = auth_token
        params['redirect_uri'] = self.REDIRECT_URI
        params['grant_type'] = 'authorization_code'
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
        """Obtains a new token given a refresh token.

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
        params = dict()
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        params['refresh_token'] = self.refresh_token
        # params['access_type'] = 'offline'
        # params['include_granted_scopes'] = 'true'
        params['grant_type'] = 'refresh_token'
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
        """Generates an IMAP OAuth2 authentication string.

        See https://developers.google.com/google-apps/gmail/oauth2_overview

        Args:
          username: the username (email address) of the account to authenticate
          access_token: An OAuth2 access token.
          base64_encode: Whether to base64-encode the output.

        Returns:
          The SASL argument for the OAuth2 mechanism.
        """
        auth_string = 'user={}'.format(self.username) + \
                      '\1auth=Bearer {}\1\1'.format(self.access_token)
        if base64_encode:
            auth_string = base64.b64encode(
                auth_string.encode('ascii')).decode('ascii')
        return auth_string

    def test_imap(self, auth_string):
        """Authenticates to IMAP with the given auth_string.

        Prints a debug trace of the attempted IMAP connection.

        Args:
          user: The Gmail username (full email address)
          auth_string: A valid OAuth2 string, as returned by
              generate_oauth2_string().  Must not be base64-encoded,
              since imaplib does its own base64-encoding.
        """
        print('[+] Testing IMAP connection')
        imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
        imap_conn.debug = 4
        imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
        imap_conn.select('INBOX')

    def test_smtp(self, auth_string):
        """Authenticates to SMTP with the given auth_string.

        Args:
          user: The Gmail username (full email address)
          auth_string: A valid OAuth2 string, not base64-encoded, as
              returned by generate_oauth2_string().
        """
        print('[+] Testing SMTP connection')
        smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_conn.set_debuglevel(True)
        smtp_conn.ehlo('test')
        smtp_conn.starttls()
        smtp_conn.docmd('AUTH', 'XOAUTH2 ' + auth_string)

    def get_refresh_token(self):
        return self.refresh_token

    def get_authorization(self):
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
        response = self.generate_refresh_token()
        self.access_token = response['access_token']
        self.expires_in = response['expires_in']
        return self.access_token, self.expires_in

    def send_mail(self, fromaddr, toaddr, subject, message):
        self.access_token, self.expires_in = self.refresh_authorization()
        auth_string = self.generate_oauth2_string(base64_encode=True)
        # Note: version number is tracked with bumpversion (see "setup.cfg")
        message = message + textwrap.dedent("""\n
        --
        Sent using psec version {version}
        https://pypi.org/project/python-secrets/
        https://github.com/davedittrich/python_secrets""".format(version=__version__))  # noqa
        # Encrypt message to recipient
        keyid = self.find_keyid(toaddr)
        if not keyid:
            raise RuntimeError(f"[-] no GPG key found for {toaddr}")
        encrypted_data = self.gpg.encrypt(message, keyid)
        if not encrypted_data.ok:
            raise RuntimeError(
                f"[-] GPG encryption failed: {encrypted_data.stderr}")
        encrypted_body = str(encrypted_data)

        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg.preamble = 'This is a multi-part message in MIME format.'
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        part_text = MIMEText(lxml.html.fromstring(encrypted_body).text_content().encode('utf-8'), 'plain', _charset='utf-8')  # noqa
        part_html = MIMEText(message.encode('utf-8'), 'html', _charset='utf-8')
        msg_alternative.attach(part_text)
        msg_alternative.attach(part_html)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo(self.client_id)
        server.starttls()
        server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
        server.sendmail(fromaddr, toaddr, msg.as_string())
        server.quit()


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
