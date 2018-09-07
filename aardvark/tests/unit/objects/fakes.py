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

import mock

from aardvark.objects import capabilities
from aardvark.objects import resource_provider
from aardvark.objects import resources


def make_resources(vcpu=0, memory=0, disk=0):

    res_dict = {}
    if vcpu > 0:
        res_dict.update({'VCPU': vcpu})
    if disk > 0:
        res_dict.update({'DISK_GB': disk})
    if memory > 0:
        res_dict.update({'MEMORY_MB': memory})

    return resources.Resources(res_dict)


def make_flavor(uuid, vcpus=1, ephemeral=0, root_gb=20, swap=0, ram=2000):
    flavor = {
        "uuid": uuid,
        "vcpus": vcpus,
        "ephemeral": ephemeral,
        "disk": root_gb,
        "swap": swap,
        "ram": ram
    }
    return flavor


def make_inventory_dict(ratio=1.0, reserved=0, total=10):
    return {
        'allocation_ratio': ratio,
        'reserved': reserved,
        'total': total
    }


def make_capabilities(used=None, total=None):
    used = used or make_resources()
    total = total or make_resources(vcpu=128, memory=20000, disk=80)
    return capabilities.Capabilities(used, total)


def make_resource_provider(uuid=None, name=None, capabilities=None):
    uuid = uuid or 'fake_rp_uuid'
    name = name or 'fake_rp_name'
    capabilities = capabilities or make_capabilities()
    with mock.patch('aardvark.objects.base.PlacementObjectWrapper'):
        rp = resource_provider.ResourceProvider(uuid, name)
        rp.capabilities = capabilities
        return rp
