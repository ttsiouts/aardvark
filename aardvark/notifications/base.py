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

import aardvark.conf
from aardvark.objects import base
import oslo_messaging


CONF = aardvark.conf.CONF


class NotificationEndpoint(object):
    """Base Endpoint for plugins that support the notification API."""

    event_types = []

    """List of strings to filter messages on."""

    def __init__(self):
        super(NotificationEndpoint, self).__init__()
        if self.event_types:
            self.filter_rule = oslo_messaging.NotificationFilter(
                event_type='|'.join(self.event_types))

    def _default_action(self, *args, **kwargs):
        if CONF.notification.default_action == "requeue":
            return self.requeue()
        if CONF.notification.default_action == "handled":
            return self.handled()

    def requeue(self):
        return oslo_messaging.NotificationResult.REQUEUE

    def handled(self):
        return oslo_messaging.NotificationResult.HANDLED

    audit = _default_action
    critical = _default_action
    debug = _default_action
    error = _default_action
    info = _default_action
    sample = _default_action
    warn = _default_action


class NotificationEvent(base.PersistentObject):
    """Base Notification event

    The notification payload is cast into this event as soon as the
    notification is received
    """

    def __init__(self):
        super(NotificationEvent, self).__init__()
