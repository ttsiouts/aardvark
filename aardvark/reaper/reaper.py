
from stevedore import driver

from oslo_log import log as logging

from aardvark.api.rest import nova
from aardvark.objects import project
from aardvark.objects import instance

import aardvark.conf

import collections

CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


class Reaper(object):
    """The Reaper Class

    This class decides which preemptible servers have to be terminated.
    """
    def __init__(self):
        # Load the configured driver
        self.driver = driver.DriverManager(
                "aardvark.reaper.driver",
                CONF.reaper.reaper_driver,
                invoke_on_load=True).driver
         # Load configured notification system in order to notify
         # the owner of the server that will be terminated

    def handle_request(self, request, system, slots=1):
        """Main functionality of the Reaper

        Gathers info and tries to free up the requested resources.

        :param req_spec: the request specification for the spawning server
        :param resources: the requested resources
        """
        print request
        instance_list = instance.InstanceList()
        for rp in system.resource_providers:
            servers = list()
            for project in system.preemptible_projects:
                filters = {
                    'host': rp.name,
                    'project_id': project.id_,
                    'vm_state': 'ACTIVE'
                }
                servers += instance_list.instances(**filters)
            rp.preemptible_servers = servers

        selected_hosts, selected_servers = \
            self.driver.get_preemptible_servers(request,
                                                system.resource_providers,
                                                slots)
        for server in selected_servers:
            LOG.info("Deleting server: %s" % server.name)
            self.notify_about_instance(server)
            instance_list.delete_instance(server)

    def notify_about_instance(self, instance):
        # notify with the configured notification system before deleting
        pass
