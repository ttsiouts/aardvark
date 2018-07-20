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

from oslo_context import context
from oslo_log import log
from oslo_service import service

import aardvark.conf
from aardvark import config


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


class SystemStateCalculator(service.Service):

    def __init__(self):
        super(SystemStateCalculator, self).__init__()
        self.manager = None

    def start(self):
        super(SystemStateCalculator, self).start()

        self.manager = SystemStateCalculatorManager()
        LOG.info('Starting System State Calculator')
        admin_context = context.get_admin_context()
        self.tg.add_dynamic_timer(
            self.manager.periodic_tasks,
            periodic_interval_max=CONF.periodic_interval,
            context=admin_context)

    def stop(self, graceful=True):
        super(SystemStateCalculator, self).stop(graceful=graceful)


def prepare_service(argv=None):
    log.register_options(CONF)
    log.set_defaults(default_log_levels=CONF.default_log_levels)

    argv = argv or []
    config.parse_args(argv)

    log.setup(CONF, 'aardvark')

# Move this out
from oslo_service import periodic_task
from aardvark.objects import system
from aardvark.reaper import reaper


class SystemStateCalculatorManager(periodic_task.PeriodicTasks):

    def __init__(self):
        super(SystemStateCalculatorManager, self).__init__(CONF)
        self.system = system.System()
        self.reaper = reaper.Reaper(watermark_mode=True)

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    @periodic_task.periodic_task(spacing=CONF.periodic_interval,
                                 run_immediately=True)
    def calculate_system_state(self, context, startup=True):

        LOG.debug('periodic Task timer expired')
        system_state = self.system.system_state()

        LOG.info("Calculated System usage: %s", system_state.usage())
        if system_state.usage() > CONF.aardvark.watermark:
            LOG.info("Over limit, system usage = %s" % system_state.usage()) 
            resource_request = system_state.get_excessive_resources(CONF.aardvark.watermark)

            ## Devide the resource request with the number of Resource
            ## Providers and request for more slots
            #number_rps = len(self.system.resource_providers)
            self.reaper.handle_request(resource_request, self.system)
        # Remove the cached info, to reload from the backend on the
        # next periodic run
        self.system.empty_cache()
