import sys

from oslo_config import cfg

from aardvark.api.rest import placement
from aardvark import api
from aardvark import version
from aardvark.objects import resource_provider as rp_obj
from aardvark.objects import system as system_obj

import aardvark.conf

CONF = aardvark.conf.CONF


def main():

    CONF(sys.argv[1:],
         project='aardvark',
         version=version.version_info,
         default_config_files=None)

    #system = system_obj.System()
    #print  system.state()
    client = placement.PlacementClient()
    print client.project_usages("6f1ba0d2aef44fae918a50a440900301")
