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

from aardvark.objects import base
from aardvark.objects import capabilities
from aardvark.objects import resources

class ResourceProvider(base.PlacementObjectWrapper):

    _attrs = ['uuid', 'name', 'usages', 'capabilities']

    def __init__(self, uuid, name):
        super(ResourceProvider, self).__init__(uuid=uuid, name=name)
        self.uuid = uuid
        self.name = name
        self._preemptible_servers = list()

    @property
    def preemptible_servers(self):
        return self._preemptible_servers

    @preemptible_servers.setter
    def preemptible_servers(self, new):
        self._preemptible_servers = new

    @property
    def preemptible_resources(self):
        preempt = resources.Resources()
        for server in self.preemptible_servers:
            preempt += server.resources
        return preempt

    @property
    def total_resources(self):
        return self.capabilities.total

    @property
    def used_resources(self):
        return self.capabilities.used

    @property
    def reserved_resources(self):
        return self.capabilities.reserved

    @property
    def free_resources(self):
        return self.capabilities.free_resources

    def reserve_resources(self, resources, requested):
        if resources > requested:
            self.capabilities.used -= resources - requested
        else:
            self.capabilities.used += requested - resources
        self.capabilities.reserved += requested
        
    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)


class ResourceProviderList(base.PlacementObjectWrapper):

    _attrs = ['resource_providers']

    def __init__(self, aggregates=None):
        super(ResourceProviderList, self).__init__(aggregates=aggregates)
        self.aggregates = aggregates
