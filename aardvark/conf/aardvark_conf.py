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


aardvark_group = cfg.OptGroup(
    'aardvark',
    title='Aardvark Service Options',
    help="Configuration options for Aardvark service")


aardvark_opts = [
    cfg.BoolOpt('enable_notification_handling',
                default=True,
                help="""
Enable notification hanlding

If this option is enabled, then the reaper will be triggered by error
notifications about the scheduling of an instance.
"""
    ),
    cfg.BoolOpt('enable_watermark_mode',
                default=False,
                help="""
Enable watermark mode

If this option is True, a periodic task is added to the reaper service, that
periodically posts a StateCalculation job in the Reaper's Jobboard. The reaper
will try to maintain the system usage below the configured limit by 'culling'
preemptible servers.
"""
    ),
    cfg.IntOpt('watermark',
               default=95,
               help="""
Max usage per resource class.

Represents the allowed usage percentage for each resource class. As soon as
the usage overcomes this limit, the service will try to free up resource to
keep the usage of the resource class below the watermak level.

This is taken under consideration only if the watermark mode is enabled. To
enable it, set the config option aardvark.enable_watermark_mode to True.
"""
    ),
    cfg.IntOpt('periodic_interval',
               default=10,
               help="""
Default interval (in seconds) for running periodic tasks.
"""
    ),
]


def register_opts(conf):
    conf.register_group(aardvark_group)
    conf.register_opts(aardvark_opts, group=aardvark_group)
