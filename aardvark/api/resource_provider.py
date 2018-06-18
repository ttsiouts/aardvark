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
from aardvark.objects import inventory


class ResourceProvider(object):

    def __init__(self, uuid):
        self.uuid = uuid
        self.client = client.PlacementClient()

    @property
    def usages(self):
        return self.client.usages(self.uuid)

    @property
    def all_usages(self):
        return self.client.all_usages()

    @property
    def inventories(self):
        return self.client.inventories(self.uuid)

    @property
    def resource_classes(self):
        return self.client.resource_classes()

    @property
    def capabilities(self):
        return capabilities.Capabilities.obj_from_primitive(
            self.inventories, self.usages)
