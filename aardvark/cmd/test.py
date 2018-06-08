import sys

from oslo_config import cfg

from aardvark.backend.api.rest import placement
from aardvark import version
from aardvark.objects import resource_provider as rp_obj

import aardvark.conf

CONF = aardvark.conf.CONF


def main():

    CONF(sys.argv[1:],
         project='aardvark',
         version=version.version_info,
         default_config_files=None)

    rp = rp_obj.ResourceProvider("2da6207c-5695-4fd1-bbed-a45f37b4327d")
    print rp.usages
    print rp.usages
    #pl = placement.PlacementClient()
    #print pl.inventories("2da6207c-5695-4fd1-bbed-a45f37b4327d")
    #print pl.resource_providers_inventories()
