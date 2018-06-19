from oslo_config import cfg


default_opts = [
    cfg.IntOpt('periodic_interval',
               default=10,
               help="""
Default interval (in seconds) for running periodic tasks.
"""
    ),
]


def register_opts(conf):
    conf.register_opts(default_opts)
