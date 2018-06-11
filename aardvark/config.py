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

from oslo_log import log

import aardvark.conf
from aardvark import version


CONF = aardvark.conf.CONF


def parse_args(argv, default_config_files=None, configure_db=True,
               init_rpc=True):
    log.register_options(CONF)
    log.set_defaults(default_log_levels=log.get_default_log_levels() +
                     extra_default_log_levels)
    rpc.set_defaults(control_exchange='nova')
    if profiler:
        profiler.set_defaults(CONF)

    CONF(argv[1:],
         project='nova',
         version=version.version_string(),
         default_config_files=default_config_files)