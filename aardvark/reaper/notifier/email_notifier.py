# Copyright (c) 2018 European Organization for Nuclear Research.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from email import header
from email.mime import multipart
from email.mime import text
import re
import smtplib

import aardvark.conf
from aardvark.reaper.notifier import base

from oslo_log import log as logging


CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


def _format_with_details(string, user_id, instance_uuid, instance_name):
    if user_id:
        string = string.replace('<user_id>', user_id)
    if instance_uuid:
        string = string.replace('<instance_uuid>', instance_uuid)
    if instance_name:
        string = string.replace('<instance_name>', instance_name)
    return string


def _validate_email_address(address):
    regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    def_domain = CONF.reaper_notifier.default_email_domain
    if not re.match(regex, address):
        # The only thing we can do here is to append
        # the configured default domain if the address
        # does not match to an email.
        address = "%s%s" % (address.split('@')[0], def_domain)
    return address


class EmailNotifier(base.BaseNotifier):
    """Sends an email message to the owner of an instance"""

    def __init__(self):
        super(EmailNotifier, self).__init__()

    def notify_about_instance(self, instance):
        try:
            cc = [_validate_email_address(a) for a in CONF.reaper_notifier.cc]
            bcc = [
                _validate_email_address(a) for a in CONF.reaper_notifier.bcc
            ]
            message = self.generate_message(instance, cc)
            recipients = [_validate_email_address(instance.owner)] + cc + bcc
            self.send_message(recipients, message)
        except (Exception) as e:
            LOG.error("Failed to send email message to %s regarding instance"
                      " %s because: %s",
                      _validate_email_address(instance.owner),
                      instance.uuid, e)

    def generate_message(self, instance, cc):

        subject = _format_with_details(CONF.reaper_notifier.subject,
                                       instance.user_id, instance.uuid,
                                       instance.name)

        body = _format_with_details(CONF.reaper_notifier.body,
                                    instance.user_id, instance.uuid,
                                    instance.name)

        message = multipart.MIMEMultipart('alternative')
        message.attach(text.MIMEText(body,
                                     'plain',
                                     _charset='utf-8'))

        message['From'] = CONF.reaper_notifier.sender
        message['To'] = _validate_email_address(instance.owner)

        if cc:
            message['Cc'] = ', '.join(cc)

        message['Subject'] = header.Header(subject, 'utf-8')

        return message

    def send_message(self, recipients, message):
        sender = CONF.reaper_notifier.sender
        smtp_server = CONF.reaper_notifier.smtp_server
        smtp_password = CONF.reaper_notifier.smtp_password
        con = smtplib.SMTP(smtp_server)
        if smtp_password is not None:
            con.ehlo()
            con.starttls()
            con.ehlo()
            con.login(sender, smtp_password)
        con.sendmail(from_addr=sender,
                     to_addrs=recipients,
                     msg=message.as_string())
        con.close()
