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

from __future__ import division
import collections
import itertools

from oslo_log import log as logging

import aardvark.conf
from aardvark.objects import resources as res_obj
from aardvark.reaper import strategy


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


Combination = collections.namedtuple(
    "Combination", "provider instances leftovers")


def sum_resources(x):
    resources = res_obj.Resources()
    for y in x:
        resources += y.resources
    return resources


class StrictStrategy(strategy.ReaperStrategy):

    def __init__(self, watermark_mode):
        super(StrictStrategy, self).__init__(watermark_mode=watermark_mode)

    def get_preemptible_servers(self, requested, hosts, num_instances,
                                projects):
        selected = list()
        selected_hosts = list()

        # This is the maximum number of spots that we'll try to free up
        max_allocs = num_instances * CONF.reaper.alternatives

        for host in hosts:
            host.populate(projects)

        for i in range(0, max_allocs):

            # Find all the matching flavor combinations and order them
            combo = self.find_matching_server_combinations(hosts, requested)

            if not combo:
                # If we run out of combos before the max retries break and
                # check if we have enough spots reserved.
                LOG.debug('No combo returned.')
                break

            host = combo.provider
            # Reserve the resources to enable us to reuse the host
            host.reserved_spots += 1
            if not combo.instances:
                host.used_resources += requested
            else:
                resources = sum_resources(combo.instances)
                host.used_resources -= resources - requested

            if host not in selected_hosts:
                selected_hosts.append(host)
            selected += combo.instances
            LOG.debug('List of instances: %s from host: %s selected',
                      combo.instances, combo.provider)

        if not self.watermark_mode:
            # Watermark mode is best effort. So skip this check in this
            # mode. On the other hand if we are not in watermark mode we
            # free space only if we can find the requested space.
            self.check_spots(selected_hosts, num_instances)

        return selected_hosts, selected

    def find_matching_server_combinations(self, hosts, requested):
        """Find the best matching combination

        The purpose of this feature is to eliminate the idle resources. So the
        best matching combination is the one that makes use of the most
        available space on a host.
        """
        only_free = False
        combinations = list()
        for host in hosts:
            # NOTE(ttsiouts): If free space is enough for the new server
            # then we should not delete any of the existing servers
            LOG.debug('Requested: %s, Free: %s',
                      requested, host.free_resources)
            if requested <= host.free_resources:
                LOG.debug('Free resources enough. Requested: %s, Free: %s',
                          requested, host.free_resources)
                leftovers = host.free_resources - requested
                combinations.append(Combination(provider=host,
                                                leftovers=leftovers,
                                                instances=[]))
                only_free = True
                continue

            preemptible = host.preemptible_servers
            LOG.debug('Prememptibles: %s', host.preemptible_servers)
            end = len(preemptible) + 1
            for num in range(1, end):
                num_combinations = itertools.combinations(preemptible, num)
                for combo in num_combinations:
                    resources = sum_resources(combo) + host.free_resources
                    if requested <= resources:
                        instances = [x for x in combo]
                        leftovers = resources - requested
                        combinations.append(Combination(provider=host,
                                                        leftovers=leftovers,
                                                        instances=instances))
                    else:
                        LOG.debug("Requested: %s resources: %s. combo %s, not "
                                  "selected", requested, resources, combo)

        if not combinations:
            return None

        if only_free:
            # NOTE(ttsiouts): if there is a host with free space avoid
            # deleting running VMs.
            combinations = [x for x in combinations if len(x.instances) == 0]

        return self.sort_combinations(combinations)

    def sort_combinations(self, combinations):
        """Sorts the found combinations of servers"""
        resources = sorted([
            ("VCPU", CONF.reaper.vcpu_sorting_priority),
            ("MEMORY_MB", CONF.reaper.ram_sorting_priority),
            ("DISK_GB", CONF.reaper.disk_sorting_priority)
        ], key=lambda x: x[1])

        for resource, _ in resources:
            combinations = sorted(
                combinations, key=lambda x: getattr(x.leftovers, resource, 0))
            minimum_value = getattr(combinations[0].leftovers, resource, 0)
            combinations = [
                combo for combo in combinations
                if getattr(combo.leftovers, resource, 0) == minimum_value
            ]
            if len(combinations) == 1:
                break
        return combinations[0]
