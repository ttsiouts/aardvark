from oslo_context import context
from oslo_log import log
import oslo_messaging
from oslo_service import service

import aardvark.conf
from aardvark import config
from aardvark.notifications import manager


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


class NotificationListener(service.Service):

    def __init__(self):
        super(NotificationListener, self).__init__()
        self.manager = manager.ListenerManager()

    def start(self):
        super(NotificationListener, self).start()
        LOG.info('Starting Notification listener')
        self.manager.start()

    def stop(self, graceful=True):
        super(NotificationListener, self).stop(graceful=graceful)
        self.manager.stop()


def prepare_service(argv=None):
    log.register_options(CONF)
    log.set_defaults(default_log_levels=CONF.default_log_levels)

    argv = argv or []
    config.parse_args(argv)

    log.setup(CONF, 'aardvark-notifications')
