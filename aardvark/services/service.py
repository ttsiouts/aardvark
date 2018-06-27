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
        self.reaper = reaper.Reaper()

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    @periodic_task.periodic_task(spacing=CONF.periodic_interval,
                                 run_immediately=True)
    def calculate_system_state(self, context, startup=True):

        LOG.info('periodic Task timer expired')
        system_usage = self.system.usage()

        if system_usage > CONF.aardvark.watermark:
            LOG.info("Over limit")
            resource_request = system_usage.get_excessive_resources()

            # Devide the resource request with the number of Resource
            # Providers and request for more slots
            number_rps = len(self.system.resource_providers)
            self.reaper.handle_request(resource_request/number_rps,
                                       self.system, slots=number_rps)
        # Remove the cached info, to reload from the backend on the
        # next periodic run
        self.system.empty_cache()
