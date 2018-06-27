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
