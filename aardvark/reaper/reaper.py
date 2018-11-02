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


import functools
from novaclient import exceptions as n_exc
from stevedore import driver
import time

from aardvark.api.rest import nova
from aardvark.api.rest import placement
import aardvark.conf
from aardvark import exception
from aardvark.objects import system as system_obj
from aardvark.reaper import reaper_action as ra
from aardvark.reaper import reaper_request as rr_obj
from aardvark import utils

from oslo_log import log as logging

from taskflow import exceptions as excp
from taskflow.jobs import backends


CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


def while_running(fn):
    @functools.wraps(fn)
    def wrapper(self, board):
        while self.flag:
            fn(self, board)
    return wrapper


def reaper_action(fn):
    @functools.wraps(fn)
    def wrapper(self, request):
        action = ra.ReaperAction()
        if isinstance(request, rr_obj.ReaperRequest):
            action.requested_instances = request.uuids
            action.event = request.event_type
        else:
            action.event = ra.ActionEvent.STATE_CALCULATION
        action.state = ra.ActionState.ONGOING
        action.create()
        LOG.info("Reaper action %s started", action.uuid)
        try:
            victims = fn(self, request)
            action.victims = victims
            action.state = ra.ActionState.SUCCESS
            LOG.info("Reaper action %s completed successfully", action.uuid)
        except exception.PreemptibleRequest as pr:
            action.state = ra.ActionState.CANCELED
            action.fault_reason = pr.message
            LOG.info("Reaper action %s canceled: %s", action.uuid, pr.message)
        except exception.AardvarkException as e:
            action.state = ra.ActionState.FAILED
            action.fault_reason = e.message
            LOG.info("Reaper action %s failed: %s", action.uuid, e.message)
        finally:
            action.update()
    return wrapper


class Reaper(object):
    """The Reaper Class

    This class decides which preemptible servers have to be terminated.
    """
    def __init__(self, aggregates=None):
        self.novaclient = nova.novaclient()
        self.placement = placement.PlacementClient()
        self.worker = None
        self.missed_acks = 0

        self.aggregates = aggregates if aggregates else []
        # TODO(ttsiouts): Load configured notification system in order to
        # notify the owner of the server that will be terminated

    def _load_configured_strategy(self, watermark_mode=False):
        """Loads the configured strategy"""
        return driver.DriverManager(
            "aardvark.reaper.strategy",
            CONF.reaper.strategy,
            invoke_on_load=True,
            invoke_args=tuple([watermark_mode])).driver

    def handle_reaper_request(self, request):
        try:
            victims = self._do_handle_reaper_request(request)
            self._rebuild_instances(request.uuids, request.image)
            return victims
        except exception.AardvarkException as e:
            LOG.error(e.message)
            self._reset_instances(request.uuids)
            raise

    def _do_handle_reaper_request(self, request):
        """Main functionality of the Reaper

        Gathers info and tries to free up the requested resources.

        :param req_spec: the request specification for the spawning server
        :param resources: the requested resources
        """
        # If we receive a request without explicit aggregates
        # set the aggregates of the request to self.aggregates
        # so that we don't invalidate the system state of
        # other worker threads by altering the state of resource
        # providers originally not watched by this thread.
        if request.aggregates == [] and self.aggregates[0] != []:
            request.aggregates = self.aggregates

        system = system_obj.System(request.aggregates)

        slots = len(request.uuids)
        preemptible_projects = [
            project.id_ for project in system.preemptible_projects
        ]
        if request.project_id in preemptible_projects:
            # Make space only if the requesting project is
            # non-preemptible.
            raise exception.PreemptibleRequest()
        return self.free_resources(request.resources, system, slots=slots)

    def handle_state_calculation_request(self, request):

        system = system_obj.System(request.aggregates)
        system_state = system.system_state()

        LOG.info("Current System usage = %s", system_state.usage())
        if system_state.usage() > CONF.aardvark.watermark:
            LOG.info("Over limit, attempting to cleanup")
            resource_request = system_state.get_excessive_resources(
                CONF.aardvark.watermark)

            try:
                return self.free_resources(resource_request, system,
                                           watermark_mode=True)
            except exception.RetriesExceeded:
                LOG.error("Retries exceeded while freeing resources to "
                          "maintain system usage below %s%. Aborting.",
                          CONF.aardvark.watermark)

    @utils.retries(exception.RetriesExceeded)
    def free_resources(self, request, system, slots=1, watermark_mode=False):

        reaper_strategy = self._load_configured_strategy(
            watermark_mode=watermark_mode)

        hosts = system.resource_providers
        projects = [p.id_ for p in system.preemptible_projects]

        selected_hosts, selected_servers = \
            reaper_strategy.get_preemptible_servers(request, hosts,
                                                    slots, projects)

        for server in selected_servers:
            try:
                LOG.info("Trying to delete server: %s", server.name)
                self.notify_about_instance(server)
                self.novaclient.servers.delete(server.uuid)
            except n_exc.NotFound:
                # One of the selected servers was not found so, we will retry
                LOG.info("Server %s not found. Retrying.", server.name)
                # Emptying the cached in order to retry.
                system.empty_cache()
                raise exception.RetryException()

        # We have to wait until the allocations are removed
        uuids = [s.uuid for s in selected_servers]
        if len(uuids) > 0:
            self.wait_until_allocations_are_deleted(uuids[:])

        return uuids

    def notify_about_instance(self, instance):
        # Notify with the configured notification system before deleting.
        # Leaving this here as a hook.
        pass

    def job_handler(self):
        self.flag = True

        backend_conf = {
            'board': CONF.reaper.job_backend,
            'path': "/var/lib/%s" % CONF.reaper.job_backend,
            'host': CONF.reaper.backend_host
        }

        with backends.backend("ReaperBoard", backend_conf.copy()) as board:
            self.attempt_job_claim(board)

        LOG.info("Reaper worker stopped: %s", self.aggregates)

    @while_running
    def attempt_job_claim(self, board):

        # Reset the acks in every loop to show you're alive
        self.missed_acks = 0
        jobs = board.iterjobs(ensure_fresh=True, only_unclaimed=True)
        for job in jobs:
            try:
                request = rr_obj.request_from_job(job.details)
                self._check_requested_aggregates(request.aggregates)
                board.claim(job, "worker")
                LOG.debug("Claimed %s", job)
            except exception.UnknownRequestType:
                continue
            except exception.UnwatchedAggregate:
                continue
            except (excp.UnclaimableJob, excp.NotFound):
                # Another worker maybe claimed the job. No need to
                # take further actions.
                continue

            self.handle_request(request)
            board.consume(job, "worker")
            LOG.debug("Consumed %s", job)

    @reaper_action
    def handle_request(self, request):

        if isinstance(request, rr_obj.ReaperRequest):
            return self.handle_reaper_request(request)

        elif isinstance(request, rr_obj.StateCalculationRequest):
            return self.handle_state_calculation_request(request)

    def stop_handling(self):
        self.flag = False

    def _rebuild_instances(self, uuids, image):
        for uuid in uuids:
            try:
                LOG.info("Trying to rebuild server with uuid: %s", uuid)
                self.novaclient.servers.rebuild(uuid, image)
            except n_exc.NotFound:
                # Looks like we were late, and the server is deleted.
                # Nothing more we can do.
                LOG.info("Server with uuid: %s, not found.", uuid)
                continue
            LOG.info("Request to rebuild the server %s was sent.", uuid)

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

    def _check_requested_aggregates(self, aggregates):
        if self.aggregates == []:
            return
        for aggregate in aggregates:
            if aggregate not in self.aggregates:
                raise exception.UnwatchedAggregate()

    @utils.timeit
    def wait_until_allocations_are_deleted(self, uuids, timeout=20):
        """Wait until the allocation is deleted

        Tries to get the allocations of a given instance until it's not found
        or the timeout exceeds
        """
        # Awful way to wait until the allocation is removed.....
        # Have to live with it for now... If we don't wait here, the claiming
        # of the resources will most probably fail since placement will not be
        # updated right away....
        start = time.time()
        now = start
        while now - start <= timeout:
            not_found = False
            for uuid in uuids:
                resp = self.placement.get_allocations(uuid)
                if resp['allocations'] == {}:
                    not_found = True
                    break
            if not_found:
                LOG.info('Allocations for %s not found', uuid)
                uuids.remove(uuid)
            if len(uuids) == 0:
                break
            now = time.time()
