# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import subprocess  # nosec
import textwrap

from cliff.lister import Lister


LOG = logging.getLogger(__name__)


# The TfOutput Lister assumes `terraform output` structured as
# shown here:
#
# $ terraform output -state=xgt/terraform.tfstate
# xgt = {
#   instance_user = ec2-user
#   privatekey_path = /home/dittrich/.ssh/xgt.pem
#   public_dns = ec2-52-27-37-238.us-west-2.compute.amazonaws.com
#   public_ip = 52.27.37.238
#   spot_bid_state = [active]
#   spot_bid_status = [fulfilled]
#   spot_instance_id = [i-06590cf97d79bdfd9]
# }
#
# $ terraform output -state=xgt/terraform.tfstate -json
# {
#     "xgt": {
#         "sensitive": false,
#         "type": "map",
#         "value": {
#             "instance_user": "ec2-user",
#             "privatekey_path": "/home/dittrich/.ssh/xgt.pem",
#             "public_dns": "ec2-52-27-37-238.us-west-2.compute.amazonaws.com",
#             "public_ip": "52.27.37.238",
#             "spot_bid_state": [
#                 "active"
#             ],
#             "spot_bid_status": [
#                 "fulfilled"
#             ],
#             "spot_instance_id": [
#                 "i-06590cf97d79bdfd9"
#             ]
#         }
#     }
# }
#
# Pulumi output:
# $ pulumi stack output --json
# {
#   "instance_id": "i-06a01c878aa51b66c",
#   "instance_user": "ec2-user",
#   "privatekey_path": "/home/dittrich/.ssh/xgt.pem",
#   "public_dns": "ec2-34-220-229-93.us-west-2.compute.amazonaws.com",
#   "public_ip": "34.220.229.93",
#   "subnet_id": "subnet-0e642669",
#   "vpc_id": "vpc-745d6b13"
# }


class TfOutput(Lister):
    """Retrieve current 'terraform output' results."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        tfstate = None
        try:
            tfstate = os.path.join(self.app.secrets.tmpdir_path(),
                                   "terraform.tfstate")
        except AttributeError:
            pass
        parser.add_argument('tfstate',
                            nargs='?',
                            default=tfstate,
                            help="Path to Terraform state file " +
                                 "(default: {})".format(tfstate)
                            )
        parser.epilog = textwrap.dedent("""
            If the ``tfstate`` argument is not provided, this command will
            attempt to search for a ``terraform.tfstate`` file in (1) the
            active environment's secrets storage directory (see ``environments
            path``), or (2) the current working directory. The former is
            documented preferred location for storing this file, since it
            will contain secrets that *should not* be stored in a source
            repository directory to avoid potential leaking of those secrets.

            .. code-block:: console

                $ psec environments path
                /Users/dittrich/.secrets/psec

            ..
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[*] getting terraform output')
        columns = ('Variable', 'Value')
        data = list()
        tfstate = parsed_args.tfstate
        if tfstate is None:
            base = 'terraform.tfstate'
            tfstate = os.path.join(self.app.secrets.environment_path(), base)
            if not os.path.exists(tfstate):
                tfstate = os.path.join(os.getcwd(), base)
            if not os.path.exists(tfstate):
                raise RuntimeError('[-] no terraform state file specified')
        if not os.path.exists(tfstate):
            raise RuntimeError(f"[-] file does not exist: '{tfstate}'")
        if self.app_args.verbose_level > 1:
            # NOTE(dittrich): Not DRY, but spend time fixing later.
            self.log.info(' '.join(['terraform',
                                    'output',
                                    '-state={}'.format(tfstate),
                                    '-json']))
        # >> Issue: [B607:start_process_with_partial_path] Starting a process with a partial executable path  # noqa
        #    Severity: Low   Confidence: High
        #    Location: psec/utils.py:152
        p = subprocess.Popen(['terraform',  # nosec
                              'output',
                              '-state={}'.format(tfstate),
                              '-json'],
                             env=dict(os.environ),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)
        jout, err = p.communicate()
        dout = json.loads(jout.decode('UTF-8'))
        for prefix in dout.keys():
            for k, v in dout[prefix]['value'].items():
                data.append(["{}_{}".format(prefix, k), v])
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
