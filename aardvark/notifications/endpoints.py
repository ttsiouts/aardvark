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

from functools import wraps

from aardvark.notifications import base
from aardvark.notifications import events
from aardvark import exception
from aardvark.objects import resources as resources_obj
from aardvark.objects import system as system_obj
from aardvark.reaper import reaper as reaper_obj
from aardvark.api.rest import nova

from oslo_log import log as logging


LOG = logging.getLogger(__name__)

# This has to be heavily guarded! New object and use lockutils to be sure
instance_map = {}


def retries(fn):
    # This should moved to utils
    @wraps(fn)
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < 3:
            try:
                return fn(*args, **kwargs)
            except exception.RetryException:
                retries += 1
        LOG.error('Retries exceeded!')
    return wrapper


class SchedulingEndpoint(base.NotificationEndpoint):

    event_types = ['instance.schedule']

    def __init__(self):
        super(SchedulingEndpoint, self).__init__()

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        # Add the info in a dict with the uuid as a key
        event = events.SchedulingEvent(payload)
        for uuid in event.instance_uuids:
            instance_map[uuid] = event


class StateUpdateEndpoint(base.NotificationEndpoint):

    event_types = ['instance.update']

    def __init__(self):
        super(StateUpdateEndpoint, self).__init__()
        self.novaclient = nova.novaclient()
        self.reaper = reaper_obj.Reaper()
        self.system = system_obj.System()

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        event = events.InstanceUpdateEvent(payload)
        if event.old_state == 'building' and event.new_state == 'pending':
            self.trigger_reaper(
               event.instance_uuid, event.flavor, event.image)
        else:
            # Pop instance info from the instance_map
            uuid = instance_map.pop(event.instance_uuid, None)
            if uuid:
                LOG.debug("Removed instance %s from instance map", uuid)

    @retries
    def trigger_reaper(self, uuid, flavor, image):
        
        # Enrich the request with info from the instance_map
        request = resources_obj.Resources.obj_from_payload(flavor)
        try:
            info = instance_map.pop(uuid, None)
        except KeyError:
            # Maybe there is a race. Raising RetryException to rerty
            raise exception.RetryException()

        LOG.info('Retreived info from instance_map: %s', info)
        print instance_map

        try:
            self.reaper.handle_request(request, self.system)
            LOG.info("rebuilding server with uuid: %s", uuid)
            self.novaclient.servers.rebuild(uuid, image)
        except exception.ReaperException as e:
            LOG.error(e.message)
            LOG.info('Resetting server %s to error', uuid)
            self.novaclient.servers.reset_state(uuid)

        # Cached system information is going to be used inside the Reaper.
        # Empty the cache here so they are going to be fetched again on the
        # next run.
        self.system.empty_cache()
