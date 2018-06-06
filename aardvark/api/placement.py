# Copyright (c) 2018 CERN.
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
from oslo_config import cfg


class PlacementClient(object):
    """Client class for querying Placement API"""

    def __init__(self):
        self.client = self._create_client()

    def _create_client(self):
        """Creates the client to Placement API"""
        auth_plugin = keystone_loading.load_auth_from_conf_options(
            cfg.CONF, 'placement')
        client = k_loading.load_session_from_conf_options(
            cfg.CONF, 'placement', auth=auth_plugin)
        client.additional_headers = {'accept': 'application/json'}
        return client

    def _get(self, url, **kwargs):
        return self.client.get(url, endpoint_filter=self.keystone_filter,
                               **kwargs)

    def get_resource_providers(self, filters=None):
        """Returns the resource providers from Placement API

        : param filters: A dictionary of filters to be passes to Placement API
                         If None, returns all the RPs in the system
        """
        pass
