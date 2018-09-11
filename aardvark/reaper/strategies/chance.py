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
from aardvark.objects import resources as resources_obj
from aardvark.reaper import strategy

from oslo_log import log as logging

import random


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class ChanceStrategy(strategy.ReaperStrategy):

    def __init__(self, watermark_mode=False):
        super(ChanceStrategy, self).__init__(watermark_mode=watermark_mode)

    def get_preemptible_servers(self, requested, hosts, num_instances):
        """Implements the strategy of freeing up the requested resources.

        :param req_spec: an instance of the RequestSpec class representing the
                         requested resources
        :param resources: (Why is this here?)
        """
        selected_servers = list()
        selected_hosts = list()

        # This is the maximum number of spots that we'll try to free up
        max_allocs = num_instances * CONF.reaper.alternatives

        for i in range(0, max_allocs):
            host = self.choose_host(hosts, requested)
            if not host:
                break

            servers = self.select_servers(host, requested)

            # If the host is not added and it has given servers for culling,
            # add it to the list. If a host's available are enough, then the
            # select_servers will return an empty list. But, assume, that the
            # resources were freed up in a previous round of selection. If
            # they were free since the beginning, the reaper would not have
            # been triggered.
            if host not in selected_hosts:
                selected_hosts.append(host)

            selected_servers += servers

        if not self.watermark_mode:
            # Watermark mode is best effort. So skip this check in this
            # mode. On the other hand if we are not in watermark mode we
            # free space only if we can find the requested space.
            self.check_spots(selected_hosts, requested, num_instances)

        return selected_hosts, selected_servers

    def choose_host(self, hosts, requested):
        """Random selection of the host.

        Finds the hosts that can provide the requested resources and randomly
        selects one of them.

        :param hosts: a dictionary containing the instances and flavors per
                      host mapping
        :param requested: an instance of the utils.miscellaneous.Resources
                          class representing the requested resources
        """
        valid_hosts = list()
        for host in hosts:
            resources = strategy.host_potential(
                host, host.preemptible_resources, not self.watermark_mode)
            if requested <= resources:
                # Create a list with the hosts that can potentially provide
                # the requested resources.
                valid_hosts.append(host)

        if not valid_hosts:
            return None

        return random.choice(valid_hosts)

    def select_servers(self, host, requested):
        """Selects the server(s) to cull from the provided host.

        Returns a list of randomly selected servers to be culled. At the same
        time, it reserves the resources of the selected servers in the host.
        The maximum attempts per host are specified using configuration option
        CONF.chance_driver.max_attempts.

        :param host: the selected host
        """
        max_attempts = CONF.reaper.max_attempts
        # Consider the available resources that the host can provide.
        preemptible = host.preemptible_servers

        selected = list()
        resources = resources_obj.Resources()
        # If the already available are enough, just return an empty list
        host_resources = strategy.host_potential(
            host, resources, not self.watermark_mode)
        if requested <= host_resources:
            host.reserve_resources(resources, requested)
            return selected

        # Shuffle the servers
        random.shuffle(preemptible)
        for marker in range(0, max_attempts):
            try:
                # The servers have been randomly shuffled previously so we
                # request for the preemptible server in the first position.
                server = preemptible.pop(0)
            except IndexError:
                # If we run out of servers we are stopping without killing any
                # VM. So returning an empty list
                selected = list()
                break

            selected.append(server)
            resources += server.resources

            host_resources = strategy.host_potential(
                host, resources, not self.watermark_mode)

            if host_resources >= requested:
                # This is the point we want to reach. It means that requested
                # resources will be available after the culling selected
                # servers.
                break
        else:
            # If we reach here, then the max_attempts have been reached.
            # Return an empty list.
            selected = list()

        # Reserving the selected resources in order to be able to perform
        # further computations if needed. Also we need the number of free
        # spots for the alternatives functionality

        if len(selected) > 0:
            host.reserve_resources(resources, requested)
            host.preemptible_servers = [
                pr_server for pr_server in host.preemptible_servers
                if pr_server not in selected]

        return selected
