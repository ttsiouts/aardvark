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

from oslo_log import log
from oslo_service import service

import aardvark.conf
from aardvark import config
from aardvark.notifications import manager


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


class NotificationListener(service.Service):

    def __init__(self):
        super(NotificationListener, self).__init__()
        self.manager = manager.ListenerManager()

    def start(self):
        super(NotificationListener, self).start()
        LOG.info('Starting Notification listener')
        self.manager.start()

    def stop(self, graceful=True):
        self.manager.stop()
        super(NotificationListener, self).stop(graceful=graceful)


def prepare_service(argv=None):
    log.register_options(CONF)
    log.set_defaults(default_log_levels=CONF.default_log_levels)

    argv = argv or []
    config.parse_args(argv)

    log.setup(CONF, 'aardvark-notifications')
