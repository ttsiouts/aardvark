import oslo_messaging
import aardvark.conf

CONF = aardvark.conf.CONF

class NotificationEndpoint(object):
    """Base Endpoint for plugins that support the notification API."""

    event_types = []
    
    """List of strings to filter messages on."""

    def __init__(self):
        super(NotificationEndpoint, self).__init__()
        if self.event_types:
            self.filter_rule = oslo_messaging.NotificationFilter(
                event_type='|'.join(self.event_types))

    def _default_action(self, *args, **kwargs):
        if CONF.notification.default_action == "requeue":
            return oslo_messaging.NotificationResult.REQUEUE
        if CONF.notification.default_action == "handled":
            return oslo_messaging.NotificationResult.HANDLED

    audit = _default_action 
    critical = _default_action
    debug = _default_action
    error = _default_action
    info = _default_action
    sample = _default_action
    warn = _default_action
