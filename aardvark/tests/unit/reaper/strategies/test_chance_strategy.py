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
from oslotest import base

import aardvark.conf
from aardvark.reaper.strategies import chance
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


def mocked_random(arg):
    return arg


class ChanceStrategyTests(base.BaseTestCase):

    def setUp(self):
        super(ChanceStrategyTests, self).setUp()

    @mock.patch('aardvark.reaper.strategies.chance.ChanceStrategy.'
                'choose_host')
    @mock.patch('aardvark.reaper.strategies.chance.ChanceStrategy.'
                'select_servers')
    @mock.patch('aardvark.reaper.strategy.ReaperStrategy.check_spots')
    def test_get_preemptible_servers(self, spots, select, choose):
        selected_hosts, selected_servers = ((['host1'], ['server1']))
        choose.return_value = selected_hosts[0]
        select.return_value = selected_servers
        strategy = chance.ChanceStrategy(watermark_mode=False)
        CONF.reaper.alternatives = 1

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        self.assertEqual((selected_hosts, selected_servers),
                         strategy.get_preemptible_servers(requested, None, 1))
        spots.assert_called_once_with(selected_hosts, requested, 1)

    def test_choose_host(self):
        strategy = chance.ChanceStrategy(watermark_mode=False)

        pre1 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        free1 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        pre2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        free2 = object_fakes.make_resources()

        hosts = [
            mock.Mock(free_resources=free1, preemptible_resources=pre1),
            mock.Mock(free_resources=free2, preemptible_resources=pre2)
        ]

        request = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)

        with mock.patch('random.choice') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual(hosts, strategy.choose_host(hosts, request))
            strategy.watermark_mode = True
            self.assertEqual([hosts[1]], strategy.choose_host(hosts, request))

    def test_choose_host_not_equal_resources(self):
        strategy = chance.ChanceStrategy(watermark_mode=False)

        pre1 = object_fakes.make_resources(vcpu=3, disk=10)
        free1 = object_fakes.make_resources(vcpu=1, memory=512, disk=10)

        pre2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        free2 = object_fakes.make_resources()

        hosts = [
            mock.Mock(free_resources=free1, preemptible_resources=pre1),
            mock.Mock(free_resources=free2, preemptible_resources=pre2)
        ]

        request = object_fakes.make_resources(vcpu=4)

        with mock.patch('random.choice') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual(hosts, strategy.choose_host(hosts, request))
            strategy.watermark_mode = True
            self.assertEqual([hosts[1]], strategy.choose_host(hosts, request))

    def test_select_servers(self):
        strategy = chance.ChanceStrategy(watermark_mode=True)

        pre = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        free = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        servers = [
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), _id='server1'),
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), _id='server2'),
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), _id='server3')
        ]

        host = mock.Mock(free_resources=free, preemptible_resources=pre,
                         preemptible_servers=servers)
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            expected = servers[0].resources + servers[1].resources
            self.assertEqual([servers[0], servers[1]],
                             strategy.select_servers(host, requested))
            host.reserve_resources.assert_called_once_with(expected, requested)
            self.assertEqual(1, len(servers))
            self.assertEqual('server3', servers[0]._id)

    def test_select_servers_enough_free(self):
        strategy = chance.ChanceStrategy(watermark_mode=False)

        pre = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        free = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        host = mock.Mock(free_resources=free, preemptible_resources=pre)

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        self.assertEqual([], strategy.select_servers(host, requested))
        host.reserve_resources.assert_called_once_with(
            object_fakes.make_resources(), requested)

    def test_select_servers_not_enough_resources(self):
        strategy = chance.ChanceStrategy(watermark_mode=False)
        CONF.reaper.max_attempts = 10
        pre = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        free = object_fakes.make_resources()

        servers = [
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), _id='server1'),
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), _id='server2'),
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), _id='server3')
        ]

        host = mock.Mock(free_resources=free, preemptible_resources=pre,
                         preemptible_servers=servers)
        requested = object_fakes.make_resources(vcpu=6, memory=512, disk=10)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual([], strategy.select_servers(host, requested))
            self.assertTrue(not host.reserve_resources.called)

    def test_select_servers_out_of_retries(self):
        strategy = chance.ChanceStrategy(watermark_mode=False)
        CONF.reaper.max_attempts = 2
        pre = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        free = object_fakes.make_resources()

        servers = [
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), _id='server1'),
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), _id='server2'),
            mock.Mock(resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), _id='server3')
        ]

        host = mock.Mock(free_resources=free, preemptible_resources=pre,
                         preemptible_servers=servers)
        requested = object_fakes.make_resources(vcpu=6, memory=512, disk=10)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual([], strategy.select_servers(host, requested))
            self.assertTrue(not host.reserve_resources.called)
