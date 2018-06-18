
import sys

from oslo_config import cfg
from oslo_service import service

from aardvark.services import service as aardvark_service


CONF = cfg.CONF


def main():
    # Parse config file and command line options, then start logging
    aardvark_service.prepare_service(sys.argv)

    calculator = aardvark_service.SystemStateCalculator()

    launcher = service.launch(CONF, calculator, restart_method='mutate')
    launcher.wait()
