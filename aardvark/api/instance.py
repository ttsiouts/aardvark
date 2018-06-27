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

from aardvark.api.rest import nova
from aardvark.objects import instance

class Instance(object):

    def __init__(self, uuid, name, flavor):
        self.uuid = uuid
        self.name = name
        self.flavor = flavor


class InstanceList(object):

    def __init__(self):
        self.client = nova.novaclient()

    def instances(self, **filters):
        if 'project_id' in filters:
            filters.update({'all_tenants': True})
        return [instance.Instance(server.id, server.name, server.flavor)
                for server in self.client.servers.list(search_opts=filters)]

    def delete_instance(self, instance):
        self.client.servers.delete(instance.uuid)
