
import sys

from oslo_config import cfg
from oslo_service import service

from aardvark.services import notifications as notification_service


CONF = cfg.CONF


def main():
    # Parse config file and command line options, then start logging
    notification_service.prepare_service(sys.argv)

    notification = notification_service.NotificationListener()

    launcher = service.launch(CONF, notification, restart_method='mutate')
    launcher.wait()
