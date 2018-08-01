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


from aardvark.conf import aardvark_conf
from aardvark.conf import keystone_conf
from aardvark.conf import notification_conf
from aardvark.conf import nova_conf
from aardvark.conf import placement_conf
from aardvark.conf import reaper_conf

from oslo_config import cfg


CONF = cfg.CONF


aardvark_conf.register_opts(CONF)
notification_conf.register_opts(CONF)
nova_conf.register_opts(CONF)
keystone_conf.register_opts(CONF)
placement_conf.register_opts(CONF)
reaper_conf.register_opts(CONF)
