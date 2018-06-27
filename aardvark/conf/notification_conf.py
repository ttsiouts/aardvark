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
    cfg.BoolOpt('workload_partitioning',
                deprecated_for_removal=True,
                default=False,
                help='Enable workload partitioning, allowing multiple '
                     'notification agents to be run simultaneously.'),
    cfg.MultiStrOpt('urls',
               default=["rabbit://stackrabbit:password@127.0.0.1:5672/"],
               secret=True,
               help="Messaging URL to listen for Nova notifications."),
    cfg.IntOpt('workers',
               default=1,
               min=1,
               help='Number of workers for notification service, '
               'default value is 1.'),
    cfg.MultiStrOpt("topics",
        default=["versioned_notifications"],
        help="""Set the topics where the listeners should subscribe to"""),
]


def register_opts(conf):
    conf.register_group(notification_group)
    conf.register_opts(notification_opts, group=notification_group)
