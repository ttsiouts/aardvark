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

import aardvark.conf
from aardvark import exception
from aardvark import utils

from oslotest import base


CONF = aardvark.conf.CONF


class UtilsTests(base.BaseTestCase):

    def setUp(self):
        super(UtilsTests, self).setUp()

    def test_retries(self):
        mocked_method = mock.Mock(__name__="mocked",
                                  side_effect=exception.RetryException())
        decorated_mocked_method = utils.retries(
            exception.AardvarkException)(mocked_method)
        self.assertRaises(exception.AardvarkException, decorated_mocked_method)
        self.assertEqual(mocked_method.call_count, 3)

    def test_retries_no_side_effect(self):
        mocked_method = mock.Mock(__name__="mocked",
                                  side_effect=exception.RetryException())
        decorated_mocked_method = utils.retries()(mocked_method)
        decorated_mocked_method()
        self.assertEqual(mocked_method.call_count, 3)

    @mock.patch('aardvark.api.rest.nova.novaclient')
    def test_map_aggregate_names(self, mock_novaclient):

        aggregates = [
            mock.Mock(uuid="agg1_uuid"),
            mock.Mock(uuid="agg2_uuid")
        ]
        aggregates[0].name = "agg1"
        aggregates[1].name = "agg2"
        CONF.reaper.watched_aggregates = ["agg1", "agg2"]
        list_method = mock.Mock(return_value=aggregates)
        mock_aggs = mock.Mock(list=list_method)
        mock_novaclient.return_value = mock.Mock(aggregates=mock_aggs)

        uuids = utils.map_aggregate_names()
        self.assertEqual([["agg1_uuid"], ["agg2_uuid"]], uuids)

    @mock.patch('aardvark.api.rest.nova.novaclient')
    def test_map_aggregate_names_bad_config(self, mock_novaclient):

        aggregates = [
            mock.Mock(uuid="agg1_uuid"),
            mock.Mock(uuid="agg2_uuid")
        ]
        aggregates[0].name = "agg1"
        aggregates[1].name = "agg2"
        CONF.reaper.watched_aggregates = ["agg3"]
        list_method = mock.Mock(return_value=aggregates)
        mock_aggs = mock.Mock(list=list_method)
        mock_novaclient.return_value = mock.Mock(aggregates=mock_aggs)

        self.assertRaises(exception.BadConfigException,
                          utils.map_aggregate_names)
