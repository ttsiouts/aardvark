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
from aardvark.reaper import notifier
from aardvark.reaper import reaper_action as ra
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes


CONF = aardvark.conf.CONF


class ReaperNotifierTests(base.TestCase):

    notifier_name = ""

    def setUp(self):
        super(ReaperNotifierTests, self).setUp()
        self.notifier = None

    def test_notifier_name(self):
        if self.notifier:
            self.assertEqual(self.notifier_name, self.notifier.name)


class LogNotifierTests(ReaperNotifierTests):

    notifier_name = "LogNotifier"

    def setUp(self):
        super(LogNotifierTests, self).setUp()
        self.notifier = notifier.LogNotifier()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    def test_notify_about_instance(self, mock_log):
        instance = mock.Mock(uuid='fake-uuid')
        msg = "Preemptible instance %s was deleted."
        self.notifier.notify_about_instance(instance)
        mock_log.assert_called_once_with(msg, instance.uuid)

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action(self, mock_error, mock_info):
        action = fakes.make_reaper_action()
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, "
               "requested instances: %s, event: %s")
        mock_info.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower())
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_success(self, mock_error, mock_info):
        action = fakes.make_reaper_action(state=ra.ActionState.SUCCESS)
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, requested instances: %s,"
               " event: %s, victims: %s")
        mock_info.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower(),
            action.victims)
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_fail(self, mock_error, mock_info):
        action = fakes.make_reaper_action(state=ra.ActionState.FAILED,
                                          fault_reason="Action failed")
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, requested instances: %s,"
               " event: %s, fault reason: %s")
        mock_error.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower(),
            action.fault_reason)
        mock_info.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_canceled(self, mock_error, mock_info):
        action = fakes.make_reaper_action(state=ra.ActionState.CANCELED,
                                          fault_reason="Action canceled")
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, requested instances: %s,"
               " event: %s, fault reason: %s")
        mock_error.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower(),
            action.fault_reason)
        mock_info.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc(self, mock_error, mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION)
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s"
        mock_info.assert_called_once_with(msg, action.uuid,
                                          action.state.value.lower())
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc_succ(self, mock_error, mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION,
            state=ra.ActionState.SUCCESS)
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s, victims: %s"
        mock_info.assert_called_once_with(msg, action.uuid,
                                          action.state.value.lower(),
                                          action.victims)
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc_fail(self, mock_error, mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION,
            state=ra.ActionState.FAILED, fault_reason="Action failed")
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s, fault reason: %s"
        mock_error.assert_called_once_with(msg, action.uuid,
                                           action.state.value.lower(),
                                           action.fault_reason)
        mock_info.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc_canceled(self, mock_error,
                                                     mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION,
            state=ra.ActionState.CANCELED, fault_reason="Action canceled")
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s, fault reason: %s"
        mock_error.assert_called_once_with(msg, action.uuid,
                                           action.state.value.lower(),
                                           action.fault_reason)
        mock_info.assert_not_called()
