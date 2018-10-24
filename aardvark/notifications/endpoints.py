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

from novaclient import exceptions as n_exc
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class SchedulingEndpoint(base.NotificationEndpoint):

    event_types = ['instance.schedule']

    def __init__(self):
        super(SchedulingEndpoint, self).__init__()

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        # Store the info in the database
        LOG.info("Received new scheduling info")
        event = events.SchedulingEvent.from_payload(payload)
        try:
            event.create()
        except exception.DBException:
            LOG.error("An exception occured while storing scheduling info "
                      "for request_id: %s", event.request_id)
            pass
        return self._default_action()


class StateUpdateEndpoint(base.NotificationEndpoint):

    event_types = ['instance.update']

    def __init__(self):
        super(StateUpdateEndpoint, self).__init__()
        self.novaclient = nova.novaclient()
        self.job_manager = job_manager.JobManager()

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        event = events.StateUpdateEvent.from_payload(payload)
        if event.is_failed_build() or event.is_failed_rebuild():
            event_type = "build" if event.is_failed_build() else "rebuild"
            # Persist the event here, since it's of interest.
            event.create()
            event.set_handled()
            try:
                self.trigger_reaper(
                    event.instance_uuid, event.flavor, event.image, event_type)
            except exception.RetriesExceeded:
                LOG.debug("Couldn't find the scheduling info for instance"
                          "%s. Returning.")
                return self.requeue()
        return self._default_action()

    @utils.retries(exception.RetriesExceeded)
    def trigger_reaper(self, uuid, flavor, image, event_type):
        try:
            # No default value in order to retry
            info = events.SchedulingEvent.get_by_instance_uuid(uuid)
            info.set_handled(instance_uuid=uuid, handled=True)
        except exception.DBException:
            # Maybe there is a race. Raising RetryException to rerty
            LOG.debug('Retrying to retrieve info for uuid <%s>', uuid)
            raise exception.RetryException()

        if info.retries >= 5:
            LOG.info("Retries for instance %s exceeded. Setting event to "
                     "handled and returning", uuid)
            return

        LOG.info("Notification received for uuid: %s event type: %s",
                 uuid, event_type)
        # Enrich the request with info from the scheduling_info
        request = resources_obj.Resources.obj_from_payload(flavor)

        uuids = info.instance_uuids

        if info.multiple_instances and event_type != "rebuild":
            unhandled_events = info.count_scheduling_instances(handled=False)
            if unhandled_events != 0:
                # Wait until the last instance for this request is set to the
                # Pending state, bundle the requests and trigger the reaper
                # once for all of them.
                LOG.info('Bundling up requests for multiple instances.')
                return

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
