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

from aardvark.api.rest import keystone
from aardvark.objects import project as pr_obj

class Project(object):

    def __init__(self, id_, name, preemptible=False):
        self.id_ = id_
        self.name = name
        self.client = keystone.KeystoneClient()


class ProjectList(object):

    def __init__(self):
        self.client = keystone.KeystoneClient()

    @property
    def projects(self):
        # Pluggable filters
        projects = []
        for project in self.client.get_projects():
            try:
                projects.append(pr_obj.Project(
                    project['id'], project['name'], project['preemptible'])) 
            except KeyError:
                projects.append(pr_obj.Project(
                    project['id'], project['name']))
        return projects

    @property
    def preemptible_projects(self):
        # Pluggable filters
        projects = []
        for project in self.client.get_projects(tags=['preemptible']):
            projects.append(pr_obj.Project(
                project['id'], project['name'], preemptible=True))
        return projects
