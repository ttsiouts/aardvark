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

from keystoneauth1 import exceptions as keystone_exc
from keystoneauth1 import loading as keystone_loading

import aardvark.conf


CONF = aardvark.conf.CONF


def exception_map(f):
    """Catches keystone exceptions

    Wraper that tries to catch excetpions from keystone and map them to
    aardvark equivalents.
    """
    def wrapper(self, *a, **k):
        try:
            return f(self, *a, **k)
        except keystone_exc.NotFound:
            # TODO: map the exceptions
            return None
    return wrapper


def object_map(f):
    """Catches keystone exceptions
    """
    @exception_map
    def map_response_to_object(self, *a, **k):
        """Maps Placement response to object"""
        response, obj = f(self, *a, **k)

        if not response:
            return None

        json = response.json()
        if not obj:
            return json

        # Map the json to the given object
        module = __import__('aardvark.objects')
        cls = getattr(module, obj)
        return cls.from_dict()

    return map_response_to_object


class PlacementClient(object):
    """Client class for querying Placement API"""

    keystone_filter = {'service_type': 'placement'}

    def __init__(self):
        self.client = self._create_client()

    def _create_client(self):
        """Creates the client to Placement API"""
        #import pdb; pdb.set_trace()
        auth_plugin = keystone_loading.load_auth_from_conf_options(
            CONF, 'placement')
        client = keystone_loading.load_session_from_conf_options(
            CONF, 'placement', auth=auth_plugin)
        client.additional_headers = {'accept': 'application/json'}
        return client

    @object_map
    def _get(self, url, obj=None, **kwargs):
        response = self.client.get(url, endpoint_filter=self.keystone_filter,
                                  **kwargs)
        return response, obj

    def get_resource_providers(self, filters=None):
        """Returns the resource providers from Placement API

        : param filters: A dictionary of filters to be passes to Placement API
                         If None, returns all the RPs in the system
        """
        url = '/resource_providers'
        resource_providers = self._get(url)
        return resource_providers

    def get_inventory(self, resource_provider_uuid, resource_class):
        """Get resource provider inventory.
        :param resource_provider_uuid: UUID of the resource provider
        :type resource_provider_uuid: str
        :param resource_class: Resource class name of the inventory to be
          returned
        :type resource_class: str
        :raises c_exc.PlacementInventoryNotFound: For failure to find inventory
          for a resource provider
        """
        url = '/resource_providers/%s/inventories/%s' % (
            resource_provider_uuid, resource_class)
        return self._get(url)

    def get_provider_usages(self, resource_provider):
        """Returns the usages of a given provider

        :param resource_provider: the provider to search for
        """
        # obj = 'Usage'
        url = "resource_providers/%s/usages" % resource_provider
        # response = self._get(url, obj)
        response = self._get(url)
        return response
