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

import collections
from oslo_db.sqlalchemy import session as db_session
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import text

import aardvark.conf
from aardvark.db import placement_api
from aardvark.db.sqlalchemy.placement_api_models import Allocation
from aardvark.db.sqlalchemy.placement_api_models import PlacementAggregate
from aardvark.db.sqlalchemy.placement_api_models import ResourceProvider as RP


Inventory = collections.namedtuple(
    'Inventory', 'total allocation_ratio reserved'
)


ResourceClasses = {
    '0': 'VCPU',
    '1': 'MEMORY_MB',
    '2': 'DISK_GB'
}

CONF = aardvark.conf.CONF
_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade(CONF.compute.placement_api_db)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    return PlacementApiConnection()


def model_query(model, *args, **kwargs):
    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


def execute_query(query):
    engine = get_engine()
    query = text(query)
    return engine.execute(query)


class PlacementApiConnection(placement_api.PlacementApiConnection):
    """Base class for storage connections."""

    def __init__(self):
        pass

    def list_resource_providers_by_instances(self, instances):
        session = get_session()
        query = (session.query(Allocation, RP)
                 .join(RP, and_(Allocation.resource_provider_id == RP.id,
                                Allocation.resource_class_id == 0,
                                Allocation.consumer_id.in_(instances)))
                 .group_by(RP.id)
                 )
        try:
            return query.all()
        except NoResultFound:
            return []

    def show_placement_aggregate(self, agg, instances):
        session = get_session()
        query = model_query(PlacementAggregate)
        query = query.filter_by(uuid=agg)
        query = (session.query(Allocation, RP, )
                 .join(RP, and_(Allocation.resource_provider_id == RP.id,
                                Allocation.consumer_id.in_(instances)))
                 .join()
                 .group_by(RP.id)
                 )
        return query.all()

    def candidate_resource_providers(self, preemptible_projects=None,
                                     aggregates=None, limit=5):
        preemptible = ", ".join("'%s'" % proj for proj in preemptible_projects)
        aggregates = ", ".join("'%s'" % agg for agg in aggregates)
        query = (
            "select resource_providers.id, resource_providers.uuid, "
            "resource_providers.name, sum(allocations.used) as total "
            "from projects join consumers on "
            "projects.id = consumers.project_id "
            "join allocations on allocations.consumer_id = consumers.uuid "
            "join resource_providers on "
            "resource_providers.id = allocations.resource_provider_id "
            "join resource_provider_aggregates "
            "on resource_provider_aggregates.resource_provider_id = "
            "resource_providers.id join placement_aggregates on "
            "placement_aggregates.id = "
            "resource_provider_aggregates.aggregate_id "
            "where projects.external_id in (%s) and "
            "placement_aggregates.uuid in (%s) and "
            "allocations.resource_class_id = 1 "
            "group by resource_providers.uuid "
            "order by total desc limit %s" % (preemptible, aggregates, limit)
        )
        result = execute_query(query)

        resource_providers = {rp[1]: (rp[0], rp[2]) for rp in result}
        candidates = {}
        if not resource_providers:
            return candidates

        rps = ", ".join("'%s'" % rp for rp in resource_providers.keys())

        inventories = self._get_inventories(rps)
        usages = self._get_used_resources(rps)
        preemptibles = self._get_preemptible_consumers(preemptible, rps)

        for rp in resource_providers:
            candidates[rp] = {
                'id': resource_providers[rp][0],
                'uuid': rp,
                'name': resource_providers[rp][1],
                'inventories': inventories[rp],
                'usages': usages[rp],
                'preemptibles': preemptibles[rp]
            }

        return candidates

    def _get_used_resources(self, resource_providers):
        used = (
            "select resource_providers.uuid, sum(allocations.used), "
            "allocations.resource_class_id from resource_providers join "
            "allocations on resource_providers.id = "
            "allocations.resource_provider_id  "
            "where resource_providers.uuid in (%s) "
            "group by allocations.resource_class_id, "
            "resource_providers.uuid" % resource_providers
        )
        result = execute_query(used)
        usages = collections.defaultdict(dict)
        for row in result:
            resource_class = ResourceClasses[str(row[2])]
            usages[row[0]][resource_class] = int(row[1])
        return usages

    def _get_inventories(self, resource_providers):
        query = (
            "select resource_providers.uuid, inventories.resource_class_id, "
            "inventories.total, inventories.allocation_ratio, "
            "inventories.reserved from inventories "
            "join resource_providers "
            "on resource_providers.id = inventories.resource_provider_id "
            "where resource_providers.uuid in (%s)" % resource_providers
        )
        result = execute_query(query)
        inventories = collections.defaultdict(dict)
        for row in result:
            resource_class = ResourceClasses[str(row[1])]
            rc_inv = Inventory(row[2], row[3], row[4])
            inventories[row[0]][resource_class] = rc_inv

        return inventories

    def _get_preemptible_consumers(self, preemptible_projects,
                                   resource_providers):
        query = (
            "select resource_providers.uuid, consumers.uuid, "
            "users.external_id, allocations.used, "
            "allocations.resource_class_id from allocations "
            "join consumers on allocations.consumer_id = consumers.uuid "
            "join resource_providers "
            "on resource_providers.id = allocations.resource_provider_id "
            "join projects on projects.id = consumers.project_id "
            "join users on users.id = consumers.user_id "
            "where projects.external_id in (%s) "
            "and resource_providers.uuid in (%s)" % (preemptible_projects,
                                                     resource_providers)
        )
        result = execute_query(query)
        preemptibles = collections.defaultdict(dict)
        for row in result:
            resource_class = ResourceClasses[str(row[4])]
            if row[1] not in preemptibles[row[0]]:
                preemptibles[row[0]][row[1]] = collections.defaultdict(dict)
            preemptibles[row[0]][row[1]][resource_class] = row[3]
            preemptibles[row[0]][row[1]]['user_id'] = row[2]
            preemptibles[row[0]][row[1]]['uuid'] = row[1]

        return preemptibles
