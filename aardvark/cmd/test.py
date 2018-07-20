import sys
import oslo_messaging
from oslo_config import cfg

from aardvark.api.rest import placement
from aardvark.api.rest import nova
from aardvark.api import project
from aardvark import api
from aardvark import version
from aardvark.objects import resource_provider as rp_obj
from aardvark.objects import system as system_obj

import aardvark.conf

import time
CONF = aardvark.conf.CONF


class NotificationEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id='^.*$')

    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        print "warn"
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        print "info"
        print event_type
        print payload

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        print "error"

def main():

    CONF(sys.argv[1:],
         project='aardvark',
         version=version.version_info,
         default_config_files=None)

    #system = system_obj.System()
    #print  system.state()
    #client = placement.PlacementClient()
    #print client.project_usages("6f1ba0d2aef44fae918a50a440900301")
    #pr = project.ProjectList()
    #print pr.projects
    client = nova.novaclient()
    #print client.servers.list(search_opts={'all_tenants': True, 'host':'ttsiouts-preemptible-cloud-1.cern.ch', 'project': 'a966b7fc224e4183aa9efe082401e7e2'})
    #print client.servers.list(search_opts={'project_id': '6f1ba0d2aef44fae918a50a440900301'})
    #print client.servers.list()
    import pdb; pdb.set_trace()
    print client.cells.get('6e3b1f3b-2263-4433-bc9c-696597fb3ce2')


#def main():
#    register_keystoneauth_opts(CONF)
#    CONF(sys.argv[1:], version='1.0.17',
#         default_config_files=config.find_config_files())

#    transport = oslo_messaging.get_notification_transport(CONF, CONF.notification.url)
#    targets = [oslo_messaging.Target(topic=CONF.notification.notification_topic)]
#    endpoints = [NotificationEndpoint()]
#
#    server = oslo_messaging.get_notification_listener(transport,
#                                                      targets,
#                                                      endpoints,
#                                                      executor='threading')
#    print "Starting"
#    server.start()
#    try:
#        while True:
#            time.sleep(1)
#    except KeyboardInterrupt:
#        print "Stopping, be patient"
#        server.stop()
#        server.wait() 
