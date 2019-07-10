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


reaper_notifier_group = cfg.OptGroup(
    'reaper_notifier',
    title='Aardvark Notifiers Options',
    help="Configuration options for Aardvark notifiers")

reaper_notifier_opts = [
    cfg.ListOpt('enabled_notifiers',
                default=['log'],
                help="""
This specifies a list of notifiers to be used uppon deleting an instance. The
possible options would be the following:

* log:   Uses python logging to log the action
"""
    ),
]


def register_opts(conf):
    conf.register_group(reaper_notifier_group)
    conf.register_opts(reaper_notifier_opts, group=reaper_notifier_group)
