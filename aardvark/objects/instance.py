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

from aardvark.api import nova
from aardvark.api import placement
import aardvark.conf
from aardvark.objects import base
from aardvark.objects import resources


CONF = aardvark.conf.CONF

class Instance(base.BaseObject):

    def __init__(self, uuid, name, flavor, user_id, metadata, image, rp_uuid):
        super(Instance, self).__init__(uuid, name, flavor, user_id, metadata,
                                       image, rp_uuid)
        self.uuid = uuid
        self.name = name
        self.flavor = flavor
        self.user_id = user_id
        self.metadata = metadata
        self.image = None if image == '' else image
        self.rp_uuid = rp_uuid
        self._resources = None

    @property
    def resources(self):
        if not self._resources:
            if CONF.aardvark.resources_from_flavor:
                self._resources = self._resources_from_flavor()
            else:
                self._resources = self._resources_from_placement()
        return self._resources

    def _resources_from_placement(self):
        return placement.get_consumer_allocations(self.uuid, self.rp_uuid)

    def _resources_from_flavor(self):
        return resources.Resources.obj_from_flavor(self.flavor,
                                                   is_bfv=self.is_bfv)

    @property
    def owner(self):
        return self.metadata.get('landb-responsible', self.user_id)

    @property
    def is_bfv(self):
        # It's safe to assume that if the image is None then
        # the server is most probably booting from volume
        return self.image is None

class InstanceList(base.BaseObject):

    def __init__(self):
        super(InstanceList, self).__init__()

    def instances(self, rp_uuid, **filters):
        if 'project_id' in filters:
            filters.update({'all_tenants': True})
        return [Instance(server.id, server.name, server.flavor, server.user_id,
                         server.metadata, server.image, rp_uuid)
                for server in nova.server_list(**filters)]

    def delete_instance(self, instance):
        nova.server_delete(instance)
