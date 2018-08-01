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

from keystoneauth1 import loading as keystone_loading
from novaclient import client

import aardvark.conf


CONF = aardvark.conf.CONF


def delete_server(server_uuid):
    """Deletes the given server"""
    pass


def rebuild_server(server_uuid):
    """Rebuilds the given server"""
    pass


def novaclient():
    auth_plugin = keystone_loading.load_auth_from_conf_options(CONF,
                                                               'compute')
    session = keystone_loading.load_session_from_conf_options(
        CONF, 'compute', auth=auth_plugin)
    return client.Client(CONF.compute.client_version, session=session)
