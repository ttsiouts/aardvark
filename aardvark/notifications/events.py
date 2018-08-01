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

from aardvark.notifications import base


class SchedulingEvent(base.NotificationEvent):
    """Scheduling Event"""

    def __init__(self, payload):
        super(SchedulingEvent, self).__init__(payload)

    @property
    def instance_uuids(self):
        return self.payload['nova_object.data']['instance_uuids']

    @property
    def request_spec(self):
        return self.payload['nova_object.data']['request_spec']

    @property
    def multiple_instances(self):
        return len(self.instance_uuids) > 1

    @property
    def request_id(self):
        return self.request_spec['nova_object.data']['id']

    @property
    def project_id(self):
        return self.request_spec['nova_object.data']['project_id']

    @property
    def aggregates(self):
        try:
            d = self.request_spec['nova_object.data']['requested_destination']
            return d['nova_object.data']['aggregates']
        except KeyError:
            return None


class InstanceUpdateEvent(base.NotificationEvent):
    """Instance State Update Event"""

    def __init__(self, payload):
        super(InstanceUpdateEvent, self).__init__(payload)
        self.state_update = self.payload['nova_object.data']['state_update']

    @property
    def instance_uuid(self):
        return self.payload['nova_object.data']['uuid']

    @property
    def old_state(self):
        return self.state_update['nova_object.data']['old_state']

    @property
    def new_state(self):
        return self.state_update['nova_object.data']['state']

    @property
    def image(self):
        return self.payload['nova_object.data']['image_uuid']

    @property
    def flavor(self):
        return self.payload['nova_object.data']['flavor']['nova_object.data']
