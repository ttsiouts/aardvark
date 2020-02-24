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

from aardvark.db import nova_cell_api as db_api
from aardvark.objects import base
from aardvark.objects import resources


class Instance(base.NovaLoadedObject):

    def __init__(self, id, uuid, name, user_id, vcpus, memory_mb, root_gb,
                 ephemeral_gb, metadata, image, flavor_id, created):
        self.id = id
        self.uuid = uuid
        self.name = name
        self.user_id = user_id
        self.image = image
        self.metadata = {meta.key: meta.value for meta in metadata}
        instance_resources = {
            'VCPU': vcpus,
            'DISK_GB': root_gb + ephemeral_gb,
            'MEMORY_MB': memory_mb
        }
        self.resources = resources.Resources(resources=instance_resources)
        self.flavor = {'original_name': flavor_id}
        self.created = created

    @staticmethod
    def from_db_object(db_object):
        return Instance(db_object.id, db_object.uuid, db_object.hostname,
                        db_object.user_id, db_object.vcpus,
                        db_object.memory_mb, db_object.root_gb,
                        db_object.ephemeral_gb, db_object.meta,
                        db_object.image_ref, db_object.instance_type_id,
                        db_object.created_at)

    @staticmethod
    def list_instances(cell_name):
        dbapi = db_api.get_instance()
        db_objects = dbapi.list_instances(cell_name)
        return [Instance.from_db_object(obj) for obj in db_objects]
