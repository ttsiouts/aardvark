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

from aardvark.api.rest import placement as client
from aardvark.objects import capabilities
from aardvark.objects import resource_provider as rp_obj
from aardvark.objects import resources


class ResourceProvider(object):

    def __init__(self, uuid, name):
        self.uuid = uuid
        self.name = name
        self.client = client.PlacementClient()

    @property
    def usages(self):
        usages = self.client.usages(self.uuid)
        return resources.Resources(usages)

    @property
    def all_usages(self):
        return self.client.all_usages()

    @property
    def inventories(self):
        inventories = self.client.inventories(self.uuid)
        return resources.Resources.obj_from_inventories(inventories)

    @property
    def resource_classes(self):
        return self.client.resource_classes()

    @property
    def capabilities(self):
        return capabilities.Capabilities(self.usages, self.inventories)


class ResourceProviderList(object):

    def __init__(self, aggregates=None):
        self.client = client.PlacementClient()
        self.aggregates = aggregates

    @property
    def resource_providers(self):
        rps = self.client.resource_providers(self.aggregates)
        return [rp_obj.ResourceProvider(rp['uuid'], rp['name']) for rp in rps]
