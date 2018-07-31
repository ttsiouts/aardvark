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


from stevedore import driver

from oslo_log import log as logging

from aardvark import exception
from aardvark.api.rest import nova
from aardvark.objects import project
from aardvark.objects import instance
from aardvark.objects import system as system_obj
from aardvark.reaper import reaper_request as rr_obj

import aardvark.conf

import time

from taskflow.jobs import backends
from taskflow import exceptions as excp

CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


SHARED_CONF = {
    'path': "/var/lib/zookeeper",
    'board': 'zookeeper',
}


class Reaper(object):
    """The Reaper Class

    This class decides which preemptible servers have to be terminated.
    """
    def __init__(self, aggregates=None, watermark_mode=False):
        self.watermark_mode = watermark_mode
        invoke_args = tuple([self.watermark_mode])
        self.novaclient = nova.novaclient()

        self.aggregates = aggregates if aggregates else []

        # Load the configured driver
        self.driver = driver.DriverManager(
                "aardvark.reaper.driver",
                CONF.reaper.reaper_driver,
                invoke_on_load=True,
                invoke_args=invoke_args).driver
        # Load configured notification system in order to notify
        # the owner of the server that will be terminated

    def handle_request(self, request):
        """Main functionality of the Reaper

        Gathers info and tries to free up the requested resources.

        :param req_spec: the request specification for the spawning server
        :param resources: the requested resources
        """

        system = system_obj.System(request.aggregates)
        slots = 1
        if not self.watermark_mode:
            slots = len(request.uuids)
            preemptible_projects = [
                project.id_ for project in system.preemptible_projects
            ]
            if request.project_id in preemptible_projects:
                # Make space only if the requesting project is
                # non-preemptible.
                raise exception.PreemptibleRequest()

        instance_list = instance.InstanceList()

        for rp in system.resource_providers:
            servers = list()
            for project in system.preemptible_projects:
                filters = {
                    'host': rp.name,
                    'project_id': project.id_,
                    'vm_state': 'ACTIVE'
                }
                servers += instance_list.instances(**filters)
            rp.preemptible_servers = servers

        selected_hosts, selected_servers = \
            self.driver.get_preemptible_servers(
                request.resources, system.resource_providers, slots)

        for server in selected_servers:
            LOG.info("Deleting server: %s" % server.name)
            self.notify_about_instance(server)
            self.novaclient.servers.delete(server.uuid)

        # Wait until allocations are removed
        time.sleep(5)

    def notify_about_instance(self, instance):
        # notify with the configured notification system before deleting
        pass

    def job_handler(self):
        self.flag = True
        with backends.backend("ReaperBoard", SHARED_CONF.copy()) as board:
            while self.flag:
                jobs = board.iterjobs(ensure_fresh=True, only_unclaimed=True)
                for job in jobs:
                    request = rr_obj.ReaperRequest.from_primitive(job.details)
                    if request.aggregates != self.aggregates:
                        # If we are in the case where one worker is looking
                        # after the whole infrastructure then we accept all
                        # requests.
                        if self.aggregates != []:
                            continue

                        # If we receive a request without explicit aggregates
                        # set the aggregates of the request to self.aggregates
                        # so that we avoid invalidating the system state of
                        # other worker threads.
                        if request.aggregates == []:
                            request.aggregates = self.aggregates
                    try:
                        board.claim(job, "worker")
                    except (excp.UnclaimableJob, excp.NotFound):
                        # Another worker maybe claimed the job. No need to
                        # take further actions.
                        continue
                    else:
                        self.take_action(request)
                        board.consume(job, "worker")
                        LOG.info("Consumed %s", job)

        LOG.info("Reaper worker stopped: %s", self.aggregates)

    def take_action(self, request):
        try:
            self.handle_request(request)
            self._rebuild_instances(request.uuids, request.image)
        except exception.ReaperException as e:
            LOG.error(e.message)
            self._reset_instances(request.uuids)

    def stop_handling(self):
        self.flag = False

    def _rebuild_instances(self, uuids, image):
        for uuid in uuids:
            LOG.info("Rebuilding server with uuid: %s", uuid)
            self.novaclient.servers.rebuild(uuid, image)

    def _reset_instances(self, uuids):
        for uuid in uuids:
            LOG.info('Resetting server %s to error', uuid)
            self.novaclient.servers.reset_state(uuid)
