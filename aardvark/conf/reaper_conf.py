from oslo_config import cfg


reaper_group = cfg.OptGroup(
    'reaper',
    title='Aardvark Service Options',
    help="Configuration options for Aardvark service")


reaper_opts = [
    cfg.StrOpt('reaper_driver',
               default='chance_driver',
               help="""
The driver that the reaper will use

Possible choices:

* strict_driver: The purpose of the preemptibles existence is to eliminate the
                 idling resources. This driver gets all the possible offers
                 from the relevant hosts and tries to find the best matching
                 for the requested resources. The best matching offer is the
                 combination of preemptible servers that leave the least
                 possible resources unused.

* chance_driver: A valid host is selected randomly and in a number of
                 preconfigured retries, the driver tries to find the instances
                 that have to be culled in order to have the requested
                 resources available.
"""
    ),
    cfg.IntOpt('alternatives',
               default=1,
               help="""
The number of alternative slots that the the reaper will try to free up for
each requested slot.
"""
    ),
    cfg.IntOpt('max_attempts',
               default=5,
               help="""
The number of alternative slots that the the reaper will try to free up for
each requested slot.
"""
    ),
]


def register_opts(conf):
    conf.register_group(reaper_group)
    conf.register_opts(reaper_opts, group=reaper_group)
