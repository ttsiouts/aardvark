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
from aardvark.db import nova_api
from aardvark.db.sqlalchemy.nova_api_models import Aggregate
from aardvark.db.sqlalchemy.nova_api_models import CellMapping
from aardvark import exception


CONF = aardvark.conf.CONF
_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade(CONF.compute.api_db)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    return NovaApiConnection()


def model_query(model, *args, **kwargs):
    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


class NovaApiConnection(nova_api.NovaApiConnection):
    """Base class for storage connections."""

    def __init__(self):
        pass

    def list_cell_mappings(self):
        query = model_query(CellMapping)
        try:
            return query.all()
        except NoResultFound:
            raise exception.InstanceSchedulingEventNotFound(uuid="")

    def list_aggregates(self):
        query = model_query(Aggregate)
        try:
            return query.all()
        except NoResultFound:
            raise exception.InstanceSchedulingEventNotFound(uuid="")

    def cell_mappings_from_aggregates(self, aggregates):
        session = get_session()
        query = (session.query(CellMapping)
                 .join(Aggregate,
                       and_(CellMapping.name == Aggregate.name,
                            CellMapping.disabled == 0,
                            Aggregate.uuid.in_(aggregates))))
        try:
            return query.all()
        except NoResultFound:
            return []
