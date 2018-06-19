from oslo_config import cfg


aardvark_group = cfg.OptGroup(
    'aardvark',
    title='Aardvark Service Options',
    help="Configuration options for Aardvark service")


aardvark_opts = [
    cfg.IntOpt('watermark',
               default=75,
               help="""
Max usage per resource class.

Represents the allowed usage percentage for each resource class. As soon as
the usage overcomes this limit, the service will try to free up resource to
keep the usage of the resource class below the watermak level.
"""
    ),
]


def register_opts(conf):
    conf.register_group(aardvark_group)
    conf.register_opts(aardvark_opts, group=aardvark_group)
