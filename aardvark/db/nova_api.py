#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc

from oslo_config import cfg
from oslo_db import api as db_api
import six


CONF = cfg.CONF
_BACKEND_MAPPING = {'nova_api': 'aardvark.db.sqlalchemy.nova_api'}

IMPL = db_api.DBAPI('nova_api',
                    backend_mapping=_BACKEND_MAPPING,
                    lazy=True,
                    use_db_reconnect=CONF.database.use_db_reconnect,
                    retry_interval=CONF.database.db_retry_interval,
                    inc_retry_interval=CONF.database.db_inc_retry_interval,
                    max_retry_interval=CONF.database.db_max_retry_interval,
                    max_retries=CONF.database.db_max_retries)


def get_instance():
    """Return a DB API instance."""
    return IMPL


@six.add_metaclass(abc.ABCMeta)
class NovaApiConnection(object):
    """Base class for storage connections."""

    @abc.abstractmethod
    def __init__(self):
        """Contructor."""

    @abc.abstractmethod
    def list_cell_mappings(self):
        """Lists cell mappings"""

    @abc.abstractmethod
    def list_aggregates(self):
        """Lists aggregates"""
