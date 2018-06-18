from oslo_config import cfg

from aardvark.conf import default_conf
from aardvark.conf import placement_conf


CONF = cfg.CONF


default_conf.register_opts(CONF)
placement_conf.register_opts(CONF)
