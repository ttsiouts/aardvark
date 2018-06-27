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
from aardvark.objects import resources

class Instance(base.BaseObjectWrapper):

    _attrs = ['name', 'uuid', 'flavor']

    def __init__(self, uuid, name, flavor):
        super(Instance, self).__init__(uuid, name, flavor)
        self.uuid = uuid
        self.name = name
        self.flavor = flavor

    @property
    def resources(self):
        return resources.Resources.obj_from_flavor(self.flavor)


class InstanceList(base.BaseObjectWrapper):

    _attrs = ['instances']

    def __init__(self):
        super(InstanceList, self).__init__()

    def instances(self, **filters):
        instances =  self._resource.instances(**filters)
        return instances

    def delete_instance(self, instance):
        self._resource.delete_instance(instance)
