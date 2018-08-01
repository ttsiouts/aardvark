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
            # TODO(ttsiouts): map the exceptions
            return None
    return wrapper


class KeystoneClient(object):
    """Client class for querying Keystone API"""

    keystone_filter = {'service_type': 'identity'}

    def __init__(self):
        self.client = self._create_client()

    def _create_client(self):
        """Creates the client to Keyston API"""
        auth_plugin = keystone_loading.load_auth_from_conf_options(
            CONF, 'identity')
        client = keystone_loading.load_session_from_conf_options(
            CONF, 'identity', auth=auth_plugin)
        client.additional_headers = {'accept': 'application/json'}
        return client

    def _get(self, url, obj=None, **kwargs):
        response = self.client.get(url, endpoint_filter=self.keystone_filter)
        return response.json()

    def get_projects(self, tags=None):
        # FIXME
        url = "/v3/projects"
        if tags is not None:
            url += "?tags=%s" % ','.join(tag for tag in tags)
        resp = self._get(url)
        return resp['projects']
