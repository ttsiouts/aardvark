from oslo_config import cfg

from aardvark.conf import aardvark_conf
from aardvark.conf import notification_conf
from aardvark.conf import nova_conf
from aardvark.conf import keystone_conf
from aardvark.conf import placement_conf
from aardvark.conf import reaper_conf


CONF = cfg.CONF


aardvark_conf.register_opts(CONF)
notification_conf.register_opts(CONF)
nova_conf.register_opts(CONF)
keystone_conf.register_opts(CONF)
placement_conf.register_opts(CONF)
reaper_conf.register_opts(CONF)
