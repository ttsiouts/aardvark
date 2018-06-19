from oslo_config import cfg

from aardvark.conf import aardvark_conf
from aardvark.conf import default_conf
from aardvark.conf import placement_conf


CONF = cfg.CONF


aardvark_conf.register_opts(CONF)
default_conf.register_opts(CONF)
placement_conf.register_opts(CONF)
