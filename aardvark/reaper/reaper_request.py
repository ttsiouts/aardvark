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


from aardvark.objects import resources as resources_obj

class ReaperRequest(object):

    def __init__(self, uuids, project_id, resources, image, aggregates=None):
        self.uuids = uuids
        self.image = image
        self.project_id = project_id
        self.resources = resources
        self.aggregates = aggregates if aggregates else []

    @staticmethod
    def from_primitive(primitive):
        uuids = primitive['uuids']
        project_id = primitive['project_id']
        image = primitive['image']
        resources = resources_obj.Resources(primitive['resources'])
        aggregates = primitive['aggregates']
        return ReaperRequest(uuids, project_id, resources, image, aggregates)

    def to_dict(self):
        return {
            'uuids': self.uuids,
            'project_id': self.project_id,
            'resources': self.resources.to_dict(),
            'image': self.image,
            'aggregates': self.aggregates
        }
