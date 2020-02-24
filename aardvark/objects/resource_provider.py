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

import collections

from aardvark.api import nova
from aardvark.api import placement
import aardvark.conf
from aardvark.objects import base
from aardvark.objects import capabilities
from aardvark.objects import instance
from aardvark.objects.nova import cell_mapping as nova_cm
from aardvark.objects.nova import resource_provider as nova_rp
from aardvark.objects import resources

from oslo_log import log


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


class ResourceProvider(base.PlacementObject):

    def __init__(self, uuid, name):
        super(ResourceProvider, self).__init__(uuid=uuid, name=name)
        self.uuid = uuid
        self.name = name
        self._preemptible_servers = list()
        self._capabilities = None
        self.reserved_spots = 0
        self.populated = False
        self.flavors_dict = collections.defaultdict(list)
        self._disabled = None
        self._usages = None
        self._inventories = None

    @staticmethod
    def from_nova_db_model(model):
        rp = ResourceProvider(model.uuid, model.name)
        rp._usages = model.usages
        rp._inventories = model.inventories
        rp.preemptible_servers = [
            instance.Instance.from_nova_db_model(ins, rp.uuid)
            for ins in model.preemptible_servers]
        rp.populated = True
        return rp

    @property
    def usages(self):
        if not self._usages:
            self._usages = placement.get_resource_provider_usages(self.uuid)
        return self._usages

    @property
    def inventories(self):
        if not self._inventories:
            self._inventories = placement.get_resource_provider_inventories(
                self.uuid)
        return self._inventories

    @property
    def resource_classes(self):
        return placement.get_resource_classes()

    @property
    def capabilities(self):
        if not self._capabilities:
            self._capabilities = capabilities.Capabilities(self.usages,
                                                           self.inventories)
        return self._capabilities

    @property
    def preemptible_servers(self):
        return self._preemptible_servers

    @preemptible_servers.setter
    def preemptible_servers(self, new):
        self._preemptible_servers = new
        self.flavors_dict = collections.defaultdict(list)
        for server in new:
            self.flavors_dict[server.flavor['original_name']].append(server)

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

    @used_resources.setter
    def used_resources(self, new):
        self.capabilities.used = new

    @property
    def reserved_resources(self):
        return self.capabilities.reserved

    @property
    def free_resources(self):
        return self.capabilities.free_resources

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    @property
    def disabled(self):
        if self._disabled is None:
            service = nova.service_status(self.name)
            self._disabled = (service.forced_down or service.state != 'up'
                              or service.status != 'enabled')
        return self._disabled

    def populate(self, preemptible_projects):
        if self.disabled:
            return
        if self.populated:
            return
        instance_list = instance.InstanceList()
        servers = list()
        for pr_project in preemptible_projects:
            filters = {
                'host': self.name,
                'project_id': pr_project,
                'vm_state': 'ACTIVE'
            }
            servers += instance_list.instances(self.uuid, **filters)
        self.preemptible_servers = servers
        self.populated = True

    def populate_sorted(self, preemptible_projects):
        if self.disabled:
            return
        if self.populated:
            return
        instance_list = instance.InstanceList()
        servers = list()
        for pr_project in preemptible_projects:
            filters = {
                'host': self.name,
                'project_id': pr_project,
                'vm_state': 'ACTIVE'
            }
            servers += instance_list.sorted_instances(self.uuid, **filters)
        self.preemptible_servers = servers
        self.populated = True

    def __repr__(self):
        return '<ResourceProvider(%s, %s)>' % (self.name, self.uuid)


class ResourceProviderList(base.PlacementObject):

    def __init__(self, aggregates=None, preemptible_projects=None):
        super(ResourceProviderList, self).__init__(aggregates=aggregates)
        self.aggregates = aggregates
        self.preemptible_projects = preemptible_projects or []

    @property
    def resource_providers(self):
        if CONF.aardvark.use_nova_api:
            return self._populated_rps_from_nova_db()
        else:
            return placement.get_resource_providers(self.aggregates)

    def _populated_rps_from_nova_db(self):
        LOG.info("Populating hosts from nova db for aggegates")
        cell_mappings = nova_cm.CellMapping.get_cell_mappings_from_aggregates(
            self.aggregates)
        rps = []
        preemptible = [p.id_ for p in self.preemptible_projects]
        for cell_mapping in cell_mappings:
            dbrps = nova_rp.ResourceProvider.list_populated_resource_providers(
                cell_mapping.name, preemptible)
            rps += [
                ResourceProvider.from_nova_db_model(dbrp) for dbrp in dbrps
            ]
        LOG.debug("Found hosts: %s", rps)
        return rps
