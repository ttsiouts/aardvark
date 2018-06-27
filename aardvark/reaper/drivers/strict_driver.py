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
import itertools
from oslo_log import log as logging
import random

import aardvark.conf
from aardvark.reaper import driver

LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class StrictDriver(driver.ReaperDriver):

    def __init__(self):
        super(StrictDriver, self).__init__()

    def get_preemptible_servers(self, requested, hosts, num_instances):
        selected = list()
        selected_hosts = list()

        # This is the maximum number of spots that we'll try to free up
        max_allocs = num_instances * CONF.reaper.alternatives

        for i in range(0, max_allocs):

            # Find all the matching flavor combinations and order them
            combo = self.find_matching_server_combinations(hosts, requested)

            if not combo:
                # If we run out of combos before the max retries break and
                # check if we have enough spots reserved.
                break

            host = hosts[combo.provider]

            # Reserve the resources to enable us to reuse the host
            host.reserve_resources(combo.consumers, requested)

            if host not in selected_hosts:
                selected_hosts.append(host)

            selected += combo.consumers

        # If we run out of combos before the max retries, we need to
        # check if we have enough spots reserved. If not, we won't
        # kill any servers. The least number of reserved spots is the
        # number of the requested instances.
        spots = 0
        for host in selected_hosts:
            spots += (host.reserved + host.available) / requested

        if spots < num_instances:
            selected = list()
            selected_hosts = list()

        return selected_hosts, selected

    def find_matching_server_combinations(self, hosts, requested):
        """Find the best matching combination

        The purpose of this feature is to eliminate the idle resources. So the
        best matching combination is the one that makes use of the most
        available space on a host.
        """
        # NOTE: Get the flavor combinations from the hosts
        combinations = list()
        for host in hosts:
             preemptible = rp.preemptible_servers()
             for num in xrange(0, len(preemptible)):
                 combiantions += itertools.combinations(preemptible, num)

        if not combinations:
            return None

        # NOTE: Order the valid combinations to find which one of them makes
        # most available space in a host. This means that the best matching
        # combination is the smallest of the valid ones!
        # e.g. requested = {vcpu: 5, memory: 1024}
        # a = {vcpu: 2, memory: 1024} and b = {vcpu: 5, memory: 1024}
        # from the valid_combos = [a, b] the best_matching would be combo 'a'
        # since it will force the host to make use of the available space
        # TODO(ttsiouts): Reuse scheduler weights for memory and disk
        return min(
            combinations, key=lambda x: (
                x.resources.VCPU,
                x.resources.MEMORY_MB,
                x.resources.DISK_GB
            )
        )
