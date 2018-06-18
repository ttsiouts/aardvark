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
from aardvark.objects import resource_provider as rp_obj
from aardvark.objects import inventory


class System(object):

    def __init__(self):
        self.client = client.PlacementClient()

    @property
    def resource_providers(self):
        rps = self.client.resource_providers()
        return [rp_obj.ResourceProvider(rp['uuid']) for rp in rps]

    @property
    def resource_classes(self):
        return (rc['name'] for rc in self.client.resource_classes())

    @property
    def traits(self):
        return (trait for trait in self.client.traits())
