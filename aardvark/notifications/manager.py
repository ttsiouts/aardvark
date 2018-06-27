from aardvark.notifications import endpoints as endpoint_objs
import oslo_messaging
import aardvark.conf

CONF = aardvark.conf.CONF

class ListenerManager(object):

    def __init__(self):
        self.listeners = []

    def _get_listeners(self):
        targets = [oslo_messaging.Target(topic=topic)
                   for topic in CONF.notification.topics]
        endpoints = [
            endpoint_objs.SchedulingEndpoint(),
            endpoint_objs.StateUpdateEndpoint()
        ]
        transports = [oslo_messaging.get_notification_transport(
            CONF, url) for url in CONF.notification.urls]
        return [oslo_messaging.get_notification_listener(
            transport, targets, endpoints, executor='threading')
            for transport in transports]

    def start(self):
        self.listeners = self._get_listeners()
        for listener in self.listeners:
            listener.start()

    def stop(self):
        for listener in self.listeners:
            listener.stop()
            listener.wait()
        self.listeners = []
