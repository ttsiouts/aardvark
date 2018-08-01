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


reaper_group = cfg.OptGroup(
    'reaper',
    title='Aardvark Service Options',
    help="Configuration options for Aardvark service")


reaper_opts = [
    cfg.StrOpt('reaper_driver',
               default='chance_driver',
               help="""
The driver that the reaper will use

Possible choices:

* strict_driver: The purpose of the preemptibles existence is to eliminate the
                 idling resources. This driver gets all the possible offers
                 from the relevant hosts and tries to find the best matching
                 for the requested resources. The best matching offer is the
                 combination of preemptible servers that leave the least
                 possible resources unused.

* chance_driver: A valid host is selected randomly and in a number of
                 preconfigured retries, the driver tries to find the instances
                 that have to be culled in order to have the requested
                 resources available.
"""
    ),
    cfg.IntOpt('alternatives',
               default=1,
               help="""
The number of alternative slots that the the reaper will try to free up for
each requested slot.
"""
    ),
    cfg.IntOpt('max_attempts',
               default=5,
               help="""
The number of alternative slots that the the reaper will try to free up for
each requested slot.
"""
    ),
    cfg.ListOpt('watched_aggregates',
               default=[],
               help="""
The list of aggregate names that the reaper will try to make space to

Each element of the list can be an aggregate or a combination of aggregates.
Combination of aggregates is a single string with a vertical-line-separated
aggregate names.

e.g. watched_aggregates={agg_name1},{agg_name2}|{agg_name3}',....

For each element in the list, a reaper thread will be spawned and the request
will be forwarded to the responsible worker.

If the provided list is empty, only one worker will be spawned, responsible for
the whole system.
"""
    ),
    cfg.StrOpt('job_backend',
               default='redis',
               choices=('redis', 'zookeeper'),
               help="""
The backend to use for distributed task management.

For this purpose the Reaper uses OpenStack Taskflow. The two supported
backends are redis and zookeper.
"""
    ),
]


def register_opts(conf):
    conf.register_group(reaper_group)
    conf.register_opts(reaper_opts, group=reaper_group)
