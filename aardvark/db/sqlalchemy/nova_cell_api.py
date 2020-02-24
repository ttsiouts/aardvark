# Copyright (c) 2018 European Organization for Nuclear Research.
# All Rights Reserved.
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

from oslo_db.sqlalchemy import session as db_session
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

import aardvark.conf
from aardvark.db import nova_cell_api
from aardvark.db.sqlalchemy.nova_cell_models import Instance
from aardvark.db.sqlalchemy.nova_cell_models import ResourceProvider as RP
from aardvark.db.sqlalchemy import utils


CONF = aardvark.conf.CONF
_FACADE = dict()


def _create_facade_lazily(cell_name):
    global _FACADE
    try:
        return _FACADE[cell_name]
    except KeyError:
        _FACADE[cell_name] = db_session.EngineFacade(
            utils.get_cell_connection(cell_name))
        return _FACADE[cell_name]


def get_engine(cell_name=None):
    facade = _create_facade_lazily(cell_name)
    return facade.get_engine()


def get_session(cell_name, **kwargs):
    facade = _create_facade_lazily(cell_name)
    return facade.get_session(**kwargs)


def get_backend():
    return NovaApiConnection()


def model_query(model, cell_name, *args, **kwargs):
    session = kwargs.get('session') or get_session(cell_name)
    query = session.query(model, *args)
    return query


class NovaApiConnection(nova_cell_api.NovaCellApiConnection):
    """Base class for storage connections."""

    def __init__(self):
        pass

    def list_compute_nodes(self, cell_name):
        query = model_query(RP, cell_name)
        try:
            return query.all()
        except NoResultFound:
            return []

    def list_instances(self, cell_name):
        query = model_query(Instance, cell_name)
        try:
            return query.all()
        except NoResultFound:
            return []

    def list_populated_hosts(self, cell_name, preemptible_projects):
        session = get_session(cell_name)
        query = (session.query(Instance, RP)
                 .join(RP, and_(Instance.host == RP.hypervisor_hostname,
                                RP.deleted == 0,
                                Instance.deleted == 0,
                                Instance.project_id.in_(preemptible_projects)))
                 )
        try:
            return query.all()
        except NoResultFound:
            return []
