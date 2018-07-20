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
from aardvark.objects import resource_provider
from aardvark.objects import project
from aardvark.objects import resources
from aardvark.objects import capabilities

class System(object):

    def __init__(self):
        self._rp_list = resource_provider.ResourceProviderList()
        self._project_list = project.ProjectList()

    @property
    def resource_providers(self):
        return self._rp_list.resource_providers

    @property
    def projects(self):
        return self._project_list.projects

    @property
    def preemptible_projects(self):
        return self._project_list.preemptible_projects

    def system_state(self):
        total_resources = resources.Resources()
        used_resources = resources.Resources()
        for rp in self.resource_providers:
            total_resources += rp.total_resources
            used_resources += rp.used_resources
            rp.reinit_object()

        return capabilities.Capabilities(used_resources, total_resources)

    def empty_cache(self):
        self._rp_list.reinit_object()
        self._project_list.reinit_object()
