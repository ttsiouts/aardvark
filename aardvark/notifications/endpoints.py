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

from aardvark.notifications import base
from aardvark.objects import resources as resources_obj
from aardvark.objects import system as system_obj
from aardvark.reaper import reaper as reaper_obj
from aardvark.api.rest import nova


class SchedulingEndpoint(base.NotificationEndpoint):

    event_types = ['select_destinations']

    def __init__(self):
        super(SchedulingEndpoint, self).__init__()

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        print "Error in Scheduling"
        # Add the info in a global dict with the uuid as a key


class StateUpdateEndpoint(base.NotificationEndpoint):

    event_types = ['instance.update']

    def __init__(self):
        super(StateUpdateEndpoint, self).__init__()

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        if payload['nova_object.data']['state_update']['nova_object.data']['state'] == 'error' and \
           payload['nova_object.data']['state_update']['nova_object.data']['old_state'] == 'active':

            print "went to pending"
            flavor = payload['nova_object.data']['flavor']['nova_object.data']
            uuid = payload['nova_object.data']['uuid']
            image = payload['nova_object.data']['image_uuid']
            self.trigger_reaper(uuid, flavor, image)

    def trigger_reaper(self, uuid, flavor, image):
        reaper = reaper_obj.Reaper()
        system = system_obj.System()
        
        request = resources_obj.Resources.obj_from_payload(flavor)
        reaper.handle_request(request, system)
        novaclient = nova.novaclient()
        novaclient.servers.rebuild(uuid, image)
        #print server
