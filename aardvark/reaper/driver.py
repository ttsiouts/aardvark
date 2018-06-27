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

import time

from oslo_log import log as logging
from oslo_serialization import jsonutils

LOG = logging.getLogger(__name__)


class ReaperDriver(object):
    """The base Reaper Driver class

    This is the class that all the Drivers for the Reaper Service have to
    inherit from
    """

    def __init__(self):
        pass

    def get_preemptible_servers(self, requested, hosts, num_instances):
        # NOTE(ttsiouts): Every driver should override this method and
        # implement the strategy of the freeing
        raise NotImplementedError