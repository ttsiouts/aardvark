from oslo_config import cfg

from aardvark.conf import placement_conf

CONF = cfg.CONF

placement_conf.register_opts(CONF)
