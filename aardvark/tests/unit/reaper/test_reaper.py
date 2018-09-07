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
from novaclient import exceptions as n_exc
from oslotest import base

import aardvark.conf
from aardvark import exception
from aardvark.reaper import reaper
from aardvark.tests.unit.reaper import fakes


CONF = aardvark.conf.CONF


class ReaperTests(base.BaseTestCase):

    def setUp(self):
        super(ReaperTests, self).setUp()
        self.reaper = self._init_reaper()

    @mock.patch('aardvark.api.rest.nova.novaclient')
    @mock.patch('aardvark.api.rest.placement.PlacementClient')
    def _init_reaper(self, mock_placement, mock_novaclient):
        return reaper.Reaper()

    def test_evaluate_reaper_request(self):
        # create a request with no aggregates
        uuids = ['instance1', 'instance2']
        image = 'fake_image'
        request = fakes.make_reaper_request(uuids=uuids, image=image)
        self.reaper.aggregates = ['aggregate_1']
        self.assertNotEqual(self.reaper.aggregates, request.aggregates)
        with mock.patch.object(self.reaper, 'handle_reaper_request'):
            self.reaper.evaluate_reaper_request(request)
            # Make sure that the request has the aggregates of the reaper
            # instance.
            self.assertEqual(self.reaper.aggregates, request.aggregates)
            self.reaper.novaclient.assert_has_calls([
                mock.call.servers.rebuild('instance1', image),
                mock.call.servers.rebuild('instance2', image)
            ], any_order=True)
            self.assertTrue(
                not self.reaper.novaclient.servers.reset_state.called)

    def test_evaluate_reaper_request_error(self):
        uuids = ['instance1', 'instance2']
        request = fakes.make_reaper_request(uuids=uuids)
        self.reaper.aggregates = ['aggregate_1']
        self.assertNotEqual(self.reaper.aggregates, request.aggregates)
        with mock.patch.object(self.reaper, 'handle_reaper_request') as moc:
            moc.side_effect = exception.AardvarkException()
            self.reaper.evaluate_reaper_request(request)
            # Make sure that the request has the aggregates of the reaper
            # instance.
            self.assertEqual(self.reaper.aggregates, request.aggregates)
            self.assertTrue(not self.reaper.novaclient.servers.rebuild.called)
            self.reaper.novaclient.assert_has_calls([
                mock.call.servers.reset_state('instance1'),
                mock.call.servers.reset_state('instance2')
            ], any_order=True)

    @mock.patch('aardvark.objects.system.System')
    def test_handle_reaper_request(self, system_mock):
        project_id = 'preemptible1'
        project = [mock.Mock(_id=project_id)]
        mocked_system = mock.Mock(preemptible_projects=project)
        system_mock.return_value = mocked_system
        request = fakes.make_reaper_request(project="project1")
        with mock.patch.object(self.reaper, 'free_resources') as mocked:
            self.reaper.handle_reaper_request(request)
            mocked.assert_called_once()

    @mock.patch('aardvark.objects.system.System')
    def test_handle_state_calculation_request(self, system_mock):
        state_mock = mock.Mock(usage=mock.Mock(return_value=90))
        mocked_system = mock.Mock(
            system_state=mock.Mock(return_value=state_mock))
        system_mock.return_value = mocked_system
        CONF.aardvark.watermark = 80
        request = fakes.make_reaper_request()
        with mock.patch.object(self.reaper, 'free_resources') as mocked:
            self.reaper.handle_state_calculation_request(request)
            self.assertTrue(mocked.called)

    @mock.patch('aardvark.objects.system.System')
    def test_handle_state_calculation_request_not_needed(self, system_mock):
        state_mock = mock.Mock(usage=mock.Mock(return_value=75))
        mocked_system = mock.Mock(
            system_state=mock.Mock(return_value=state_mock))
        system_mock.return_value = mocked_system
        CONF.aardvark.watermark = 80
        request = fakes.make_reaper_request()
        with mock.patch.object(self.reaper, 'free_resources') as mocked:
            self.reaper.handle_state_calculation_request(request)
            self.assertTrue(not mocked.called)

    def test_free_resources(self):
        system = mock.Mock()
        request = fakes.make_reaper_request()
        hosts = ['host1']
        servers = [mock.Mock(uuid='server1'), mock.Mock(uuid='server2')]
        # Hack for mock's limitation with the name attribute
        for server in servers:
            server.name = server.uuid
        mocked_return = mock.Mock(return_value=(hosts, servers))
        not_found = {'allocations': {}}
        self.reaper.placement.get_allocations.return_value = not_found
        mock_strategy = mock.Mock(get_preemptible_servers=mocked_return)
        with mock.patch.object(self.reaper, '_load_configured_strategy') as m:
            m.return_value = mock_strategy
            self.reaper.free_resources(request, system)
            self.reaper.novaclient.assert_has_calls([
                mock.call.servers.delete('server1'),
                mock.call.servers.delete('server2')
            ], any_order=True)

    def test_free_resources_not_found_server(self):
        system = mock.Mock()
        request = fakes.make_reaper_request()
        self.reaper.novaclient.servers.delete.side_effect = n_exc.NotFound("")
        hosts = ['host1']
        servers = [mock.Mock(uuid='server1'), mock.Mock(uuid='server2')]
        # Hack for mock's limitation with the name attribute
        for server in servers:
            server.name = server.uuid
        mocked_return = mock.Mock(return_value=(hosts, servers))
        mock_strategy = mock.Mock(get_preemptible_servers=mocked_return)
        with mock.patch.object(self.reaper, '_load_configured_strategy') as m:
            m.return_value = mock_strategy
            self.assertRaises(exception.RetriesExceeded,
                              self.reaper.free_resources, request, system)

    # def test_attempt_job_claim(self):
    #     request = fakes.make_calculation_request()
    #     job = mock.Mock(details=request.to_dict())
    #     itermock = mock.Mock(return_value=[job])
    #     board = mock.Mock(iterjobs=itermock)
    #     self.reaper._is_running = mock.Mock()
    #     self.reaper._is_running.side_effect = ['True', 'False']
    #     with mock.patch.object(self.reaper, 'handle_request') as mocked:
    #         self.reaper.attempt_job_claim(board)
    #         mocked.assert_called_once()
    #         mocked.assert_called_with(request)

    def test_handle_request(self):
        reaper_request = fakes.make_reaper_request()
        calculation_request = fakes.make_calculation_request()
        with mock.patch.object(self.reaper, 'evaluate_reaper_request') as m:
            self.reaper.handle_request(reaper_request)
            m.assert_called_once_with(reaper_request)
        with mock.patch.object(
            self.reaper, 'handle_state_calculation_request') as m:
            self.reaper.handle_request(calculation_request)
            m.assert_called_once_with(calculation_request)

    def test_check_requested_aggregates(self):
        self.reaper.aggregates = []
        aggregates = ['agg1', 'agg2', 'agg3']
        # No exception is raised
        self.reaper._check_requested_aggregates(aggregates)

        self.reaper.aggregates = ['agg1', 'agg2', 'agg3', 'agg4']
        aggregates = ['agg1', 'agg2', 'agg3']
        # No exception is raised
        self.reaper._check_requested_aggregates(aggregates)

        self.reaper.aggregates = ['agg4']
        aggregates = ['agg1', 'agg2', 'agg3']
        self.assertRaises(exception.UnwatchedAggregate,
                          self.reaper._check_requested_aggregates, aggregates)

        self.reaper.aggregates = [1, 2, 3, 4]
        aggregates = [0, 3, 2]
        self.assertRaises(exception.UnwatchedAggregate,
                          self.reaper._check_requested_aggregates, aggregates)

    def test_wait_until_allocations_are_deleted(self):
        uuids = ['uuid1', 'uuid2']
        self.reaper.placement.get_allocations.side_effect = [
            {'allocations': {}},
            {'allocations': 'allocations_found'},
            {'allocations': {}}
        ]
        self.reaper.wait_until_allocations_are_deleted(uuids)
        self.assertEqual([], uuids)

        uuids = ['uuid1', 'uuid2']
        self.reaper.placement.get_allocations.side_effect = [
            {'allocations': {}},
            {'allocations': 'allocations_found'},
            {'allocations': 'allocations_found'},
            {'allocations': 'allocations_found'}
        ]
        with mock.patch('time.time') as mocked_time:
            mocked_time.side_effect = [1, 1, 1, 1, 100]
            self.reaper.wait_until_allocations_are_deleted(uuids)
            self.assertEqual(['uuid2'], uuids)
