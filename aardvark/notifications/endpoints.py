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


from aardvark.api.rest import nova
from aardvark import exception
from aardvark.notifications import base
from aardvark.notifications import events
from aardvark.objects import resources as resources_obj
from aardvark.reaper import job_manager
from aardvark.reaper import reaper_request as rr_obj
from aardvark import utils

import collections
from novaclient import exceptions as n_exc
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


instance_map = utils.SafeDict()


class SchedulingEndpoint(base.NotificationEndpoint):

    event_types = ['instance.schedule']

    def __init__(self):
        super(SchedulingEndpoint, self).__init__()

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        # Add the info in a dict with the uuid as a key
        event = events.SchedulingEvent(payload)
        for uuid in event.instance_uuids:
            instance_map[uuid] = event
        return self._default_action()


class StateUpdateEndpoint(base.NotificationEndpoint):

    event_types = ['instance.update']

    def __init__(self):
        super(StateUpdateEndpoint, self).__init__()
        self.novaclient = nova.novaclient()
        self.job_manager = job_manager.JobManager()
        # Use this dict to bundle up the scheduling events
        self.bundled_reqs = collections.defaultdict(list)

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        event = events.InstanceUpdateEvent(payload)
        if event.old_state == 'building' and event.new_state == 'pending':
            LOG.info("Notification received triggering reaper")
            self.trigger_reaper(
               event.instance_uuid, event.flavor, event.image)
        else:
            # Pop instance info from the instance_map in case this is about
            # another state transition.
            uuid = instance_map.pop(event.instance_uuid, None)
            if uuid:
                LOG.debug("Removed instance %s from instance map", uuid)
        return self._default_action()

    @utils.retries()
    def trigger_reaper(self, uuid, flavor, image):
        try:
            # No default value in order to retry
            info = instance_map.pop(uuid)
        except KeyError:
            # Maybe there is a race. Raising RetryException to rerty
            raise exception.RetryException()

        # Enrich the request with info from the instance_map
        request = resources_obj.Resources.obj_from_payload(flavor)

        uuids = info.instance_uuids
        request_id = info.request_id

        if info.multiple_instances:
            self.bundled_reqs[info.request_id] += [uuid]
            if len(info.instance_uuids) != len(self.bundled_reqs[request_id]):
                # Wait until the last instance for this request is set to the
                # Pending state, bundle the requests and trigger the reaper
                # once for all of them.
                LOG.info('Bundling up requests for multiple instances.')
                return
            # Remove the bundled requests after all instance update
            # notifications are received
            del self.bundled_reqs[request_id]

        reaper_request = rr_obj.ReaperRequest(
                uuids, info.project_id, request, image, info.aggregates)
        try:
            self.job_manager.post_job(reaper_request)
        except exception.ReaperException as e:
            LOG.error(e.message)
            self._reset_instances(uuids)

    def _reset_instances(self, uuids):
        for uuid in uuids:
            try:
                LOG.info('Trying to reset server %s to error', uuid)
                self.novaclient.servers.reset_state(uuid)
            except n_exc.NotFound:
                # Looks like we were late, and the server is deleted.
                # Nothing more we can do.
                LOG.info("Server with uuid: %s, not found.", uuid)
                continue
            LOG.info("Request to reset the server %s was sent.", uuid)
