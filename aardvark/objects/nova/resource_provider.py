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

from aardvark.db import placement_api as db_api
from aardvark.objects import base
from aardvark.objects.nova.instance import Instance
from aardvark.objects import resources


class ResourceProvider(base.NovaLoadedObject):

    def __init__(self, id, uuid, name, vcpus, memory_mb, local_gb, vcpus_used,
                 memory_mb_used, local_gb_used, ram_alloc, cpu_alloc,
                 disk_alloc, ram_reserved, vcpu_reserved, disk_reserved):
        self.id = id
        self.uuid = uuid
        self.name = name
        used_resources = {
            'VCPU': vcpus_used + vcpu_reserved,
            'DISK_GB': local_gb_used + disk_reserved,
            'MEMORY_MB': memory_mb_used + ram_reserved
        }
        self.usages = resources.Resources(resources=used_resources)
        inventory_resources = {
            'VCPU': vcpus * cpu_alloc,
            'DISK_GB': local_gb * disk_alloc,
            'MEMORY_MB': memory_mb * ram_alloc
        }
        self.inventories = resources.Resources(resources=inventory_resources)
        self.preemptible_servers = []

    @staticmethod
    def from_db_object(db_object):
        return ResourceProvider(db_object.id, db_object.uuid,
                                db_object.hypervisor_hostname, db_object.vcpus,
                                db_object.memory_mb, db_object.local_gb,
                                db_object.vcpus_used, db_object.memory_mb_used,
                                db_object.local_gb_used,
                                db_object.ram_allocation_ratio,
                                db_object.cpu_allocation_ratio,
                                db_object.disk_allocation_ratio,
                                db_object.disk_available_least)

    @staticmethod
    def list_resource_providers(cell_name):
        dbapi = db_api.get_instance()
        db_objects = dbapi.list_compute_nodes(cell_name)
        return [
            ResourceProvider.from_db_object(obj) for obj in db_objects
        ]

    @staticmethod
    def list_populated_resource_providers(cell_name, preemptible_projects):
        dbapi = db_api.get_instance()
        db_objects = dbapi.list_populated_hosts(cell_name,
                                                preemptible_projects)
        rps = {}
        for ins, rp in db_objects:
            ins = Instance.from_db_object(ins)
            try:

                rps[rp.uuid].preemptible_servers += [ins]
            except KeyError:
                rps[rp.uuid] = ResourceProvider.from_db_object(rp)
                rps[rp.uuid].preemptible_servers = [ins]
        return rps.values()

    @staticmethod
    def from_placemnt_db_object(db_object):
        inventories = db_object['inventories']
        usages = db_object['usages']
        rp = ResourceProvider(db_object['id'], db_object['uuid'],
                              db_object['name'],
                              inventories['VCPU'].total,
                              inventories['MEMORY_MB'].total,
                              inventories['DISK_GB'].total,
                              usages['VCPU'],
                              usages['MEMORY_MB'],
                              usages['DISK_GB'],
                              inventories['MEMORY_MB'].allocation_ratio,
                              inventories['VCPU'].allocation_ratio,
                              inventories['DISK_GB'].allocation_ratio,
                              inventories['MEMORY_MB'].reserved,
                              inventories['VCPU'].reserved,
                              inventories['DISK_GB'].reserved)
        preemptibles = db_object['preemptibles']
        for _, preemptible in preemptibles.items():
            rp.preemptible_servers += [
                Instance.from_placement_db_object(preemptible)
            ]
        return rp

    @staticmethod
    def candidate_resource_providers(preemptible_projects, aggregates):
        dbapi = db_api.get_instance()
        db_objects = dbapi.candidate_resource_providers(preemptible_projects,
                                                        aggregates)
        candidates = []
        for _, db_object in db_objects.items():
            candidates.append(
                ResourceProvider.from_placemnt_db_object(db_object)
            )
        return candidates
