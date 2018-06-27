from oslo_config import cfg


notification_group = cfg.OptGroup(
    'notification',
    title='Notification Listener Options',
    help="Configuration options for notification service")


notification_opts = [
    cfg.StrOpt("default_action",
        default="handled",
        choices=('handled', 'requeue'),
        help='Select the default action for the received notification'),
    cfg.BoolOpt('workload_partitioning',
                deprecated_for_removal=True,
                default=False,
                help='Enable workload partitioning, allowing multiple '
                     'notification agents to be run simultaneously.'),
    cfg.MultiStrOpt('urls',
               default=["rabbit://stackrabbit:password@127.0.0.1:5672/"],
               secret=True,
               help="Messaging URL to listen for Nova notifications."),
    cfg.IntOpt('workers',
               default=1,
               min=1,
               help='Number of workers for notification service, '
               'default value is 1.'),
    cfg.MultiStrOpt("topics",
        default=["versioned_notifications"],
        help="""Set the topics where the listeners should subscribe to"""),
]


def register_opts(conf):
    conf.register_group(notification_group)
    conf.register_opts(notification_opts, group=notification_group)
