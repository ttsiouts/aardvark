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
import aardvark.conf
from aardvark import exception
from aardvark.objects import system as system_obj
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


class Reaper(object):
    """The Reaper Class

    This class decides which preemptible servers have to be terminated.
    """
    def __init__(self, aggregates=None, watermark_mode=False):
        self.watermark_mode = watermark_mode
        self.novaclient = nova.novaclient()
        self.worker = None
        self.missed_acks = 0

        self.aggregates = aggregates if aggregates else []
        # TODO(ttsiouts): Load configured notification system in order to
        # notify the owner of the server that will be terminated

    def _load_configured_driver(self, watermark_mode=False):
        """Loads the configured driver"""
        return driver.DriverManager(
            "aardvark.reaper.driver",
            CONF.reaper.reaper_driver,
            invoke_on_load=True,
            invoke_args=tuple([watermark_mode])).driver

    def evaluate_reaper_request(self, request):
        # If we receive a request without explicit aggregates
        # set the aggregates of the request to self.aggregates
        # so that we don't invalidate the system state of
        # other worker threads by altering the state of resource
        # providers originally not watched by this thread.
        if request.aggregates == []:
            request.aggregates = self.aggregates

        try:
            self.handle_reaper_request(request)
            self._rebuild_instances(request.uuids, request.image)
        except exception.ReaperException as e:
            LOG.error(e.message)
            self._reset_instances(request.uuids)

    def handle_reaper_request(self, request):
        """Main functionality of the Reaper

        Gathers info and tries to free up the requested resources.

        :param req_spec: the request specification for the spawning server
        :param resources: the requested resources
        """

        system = system_obj.System(request.aggregates)

        slots = len(request.uuids)
        preemptible_projects = [
            project.id_ for project in system.preemptible_projects
        ]
        if request.project_id in preemptible_projects:
            # Make space only if the requesting project is
            # non-preemptible.
            raise exception.PreemptibleRequest()

        self.free_resources(request.resources, system, slots=slots)

        # Wait until allocations are removed
        time.sleep(5)

    def handle_state_calculation_request(self, request):

        system = system_obj.System(request.aggregates)
        system_state = system.system_state()

        LOG.info("Current System usage = %s", system_state.usage())
        if system_state.usage() > CONF.aardvark.watermark:
            LOG.info("Over limit, attempting to cleanup")
            resource_request = system_state.get_excessive_resources(
                CONF.aardvark.watermark)

            self.free_resources(resource_request, system, watermark_mode=True)

    @utils.retries
    def free_resources(self, request, system, slots=1, watermark_mode=False):

        system.populate_system_rps()
        reaper_driver = self._load_configured_driver(
            watermark_mode=watermark_mode)

        selected_hosts, selected_servers = \
            reaper_driver.get_preemptible_servers(
                request, system.resource_providers, slots)

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

    def handle_request(self, request):

        if isinstance(request, rr_obj.ReaperRequest):
            self.evaluate_reaper_request(request)

        elif isinstance(request, rr_obj.StateCalculationRequest):
            self.handle_state_calculation_request(request)

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
        l1 = [agg for agg in self.aggregates if agg in aggregates]
        l2 = [agg for agg in aggregates if agg in self.aggregates]
        if l1 != l2:
            raise exception.UnwatchedAggregate()
