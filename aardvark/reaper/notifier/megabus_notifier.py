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

import json
import time

from stompest.config import StompConfig
from stompest.sync import Stomp

import aardvark.conf
from aardvark.reaper.notifier import base

from oslo_log import log as logging


CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


class MegabusNotifier(base.BaseNotifier):
    """Sends megabus notifications when a preemtible instance is killed"""

    def __init__(self):
        super(MegabusNotifier, self).__init__()

    def notify_about_instance(self, instance):
        message = {
            'instance_uuid': instance.uuid
        }
        if instance.name is not None:
            message['instance_name'] = instance.name

        self._send_notification(message)

    def _send_notification(self, message):
        message = json.dumps(message, ensure_ascii=False)

        stomp_config = StompConfig(
            CONF.reaper_notifier.megabus_server,
            login=CONF.reaper_notifier.megabus_user,
            passcode=CONF.reaper_notifier.megabus_password)

        client = Stomp(stomp_config)
        client.connect()

        ttl = ((time.time()) + (CONF.reaper_notifier.megabus_ttl)) * 1000
        expires = {'expires': ttl}

        for queue in CONF.reaper_notifier.megabus_queues:
            LOG.debug("Sending megabus notification: %s", message)
            client.send(queue, message, expires)

        client.disconnect()
