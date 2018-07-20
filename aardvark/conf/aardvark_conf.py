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
    cfg.IntOpt('watermark',
               default=95,
               help="""
Max usage per resource class.

Represents the allowed usage percentage for each resource class. As soon as
the usage overcomes this limit, the service will try to free up resource to
keep the usage of the resource class below the watermak level.
"""
    ),
]


def register_opts(conf):
    conf.register_group(aardvark_group)
    conf.register_opts(aardvark_opts, group=aardvark_group)
