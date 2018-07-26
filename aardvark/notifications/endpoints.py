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

import collections
from functools import wraps

from aardvark.notifications import base
from aardvark.notifications import events
from aardvark import exception
from aardvark.objects import resources as resources_obj
from aardvark.objects import system as system_obj
from aardvark.reaper import reaper as reaper_obj
from aardvark.api.rest import nova

from oslo_concurrency import lockutils
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class SyncedInstanceMap(dict):
    """The internal instance to scheduling info

    Try to create a threadsafe dictionary by locking the methods needed.
    """
    @lockutils.synchronized('reaper_lock')
    def __setitem__(self, key, item):
        super(SyncedInstanceMap, self).__setitem__(key, item)

    @lockutils.synchronized('reaper_lock')
    def __getitem__(self, key):
        return super(SyncedInstanceMap, self).__getitem__(key)

    @lockutils.synchronized('reaper_lock')
    def __delitem__(self, key):
        super(SyncedInstanceMap, self).__delitem__(key)


instance_map = SyncedInstanceMap()


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
        # Use this dict to bundle up the scheduling events
        self.bundled_reqs = collections.defaultdict(list)

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        event = events.InstanceUpdateEvent(payload)
        if event.old_state == 'building' and event.new_state == 'pending':
            self.trigger_reaper(
               event.instance_uuid, event.flavor, event.image)
        else:
            # Pop instance info from the instance_map in case this is about
            # another state transition.
            uuid = instance_map.pop(event.instance_uuid, None)
            if uuid:
                LOG.debug("Removed instance %s from instance map", uuid)

    @retries
    def trigger_reaper(self, uuid, flavor, image):
        
        # Enrich the request with info from the instance_map
        request = resources_obj.Resources.obj_from_payload(flavor)
        try:
            # No default value in order to retry
            info = instance_map.pop(uuid)
        except KeyError:
            # Maybe there is a race. Raising RetryException to rerty
            raise exception.RetryException()

        uuids = info.instance_uuids
        request_id = info.request_id

        if info.multiple_instances:
            self.bundled_reqs[info.request_id]  += [uuid]
            if len(info.instance_uuids) != len(self.bundled_reqs[request_id]):
                # Wait until the last instance for this request is set to the
                # Pending state, bundle the requests and trigger the reaper
                # once for all of them.
                LOG.info('Bundling up requests for multiple instances.')
                return
            # Remove the bundled requests after all instance update
            # notifications are received
            del self.bundled_reqs[request_id]

        try:
            self.reaper.handle_request(request, self.system, info.project_id,
                                       len(uuids))
            self._rebuild_instances(uuids, image)
        except exception.ReaperException as e:
            LOG.error(e.message)
            self._reset_instances(uuids)

        # Cached system information is going to be used inside the Reaper.
        # Empty the cache here so they are going to be fetched again on the
        # next run.
        self.system.empty_cache()

    def _rebuild_instances(self, uuids, image):
        for uuid in uuids:
            LOG.info("Rebuilding server with uuid: %s", uuid)
            self.novaclient.servers.rebuild(uuid, image)

    def _reset_instances(self, uuids):
        for uuid in uuids:
            LOG.info('Resetting server %s to error', uuid)
            self.novaclient.servers.reset_state(uuid)
