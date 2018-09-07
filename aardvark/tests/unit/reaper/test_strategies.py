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

from oslotest import base

import aardvark.conf
from aardvark import exception
from aardvark.reaper.strategies import chance
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


class ReaperStrategyTests(base.BaseTestCase):

    def setUp(self):
        super(ReaperStrategyTests, self).setUp()

    def test_check_spots(self):
        used = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        total = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        capabilities = object_fakes.make_capabilities(used=used, total=total)
        hosts = [
            object_fakes.make_resource_provider(capabilities=capabilities)
        ]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        strategy = chance.ChanceStrategy(False)

        # No exception is raised
        strategy.check_spots(hosts, requested, 1)

        # Asking for two slots should raise it
        self.assertRaises(exception.NotEnoughResources,
                          strategy.check_spots, hosts, requested, 2)

    def test_check_spots_multiple_hosts(self):
        used1 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        total1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        capabilities1 = object_fakes.make_capabilities(used=used1,
                                                       total=total1)

        used2 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        total2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        capabilities2 = object_fakes.make_capabilities(used=used2,
                                                       total=total2)

        hosts = [
            object_fakes.make_resource_provider(capabilities=capabilities1),
            object_fakes.make_resource_provider(capabilities=capabilities2)
        ]

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        strategy = chance.ChanceStrategy(False)

        # No exception is raised
        strategy.check_spots(hosts, requested, 2)

        # Asking for not existing resources should raise it
        requested = hosts[0].free_resources + hosts[1].free_resources
        self.assertRaises(exception.NotEnoughResources,
                          strategy.check_spots, hosts, requested, 1)
