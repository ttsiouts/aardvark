import sys

from oslo_config import cfg

from aardvark.api.rest import placement
from aardvark import version

import aardvark.conf

CONF = aardvark.conf.CONF


def main():

    CONF(sys.argv[1:],
         project='aardvark',
         version=version.version_info,
         default_config_files=None)

    pl = placement.PlacementClient()
    print pl.get_provider_usages("2da6207c-5695-4fd1-bbed-a45f37b4327d")
