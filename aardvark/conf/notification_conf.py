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

from oslo_config import cfg


notification_group = cfg.OptGroup(
    'notification',
    title='Notification Listener Options',
    help="Configuration options for notification service")


notification_opts = [
    cfg.StrOpt("default_action",
        default="handled",
        choices=('handled', 'requeue'),
        help='Select the default action for the received notification'),
    cfg.MultiStrOpt('urls',
               default=[],
               secret=True,
               help="Messaging URL to listen for Nova notifications."),
    cfg.MultiStrOpt("topics",
        default=["versioned_notifications"],
        help="""Set the topics where the listeners should subscribe to"""),
    cfg.IntOpt('max_handling_retries',
        default=5,
        help="""
The max number of retries of handling notifications for a given instance."""),
]


def register_opts(conf):
    conf.register_group(notification_group)
    conf.register_opts(notification_opts, group=notification_group)
