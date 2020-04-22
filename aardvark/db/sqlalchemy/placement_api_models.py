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

from oslo_db.sqlalchemy.types import String
from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import orm

import aardvark.conf


CONF = aardvark.conf.CONF


def table_args():
    engine_name = 'mysql'
    if engine_name == 'mysql':
        return {'mysql_engine': CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


Base = declarative_base()


class Inventory(Base):
    __tablename__ = 'inventories'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_provider_id = Column(Integer, ForeignKey("resource_providers.id"))
    resource_class_id = Column(Integer, ForeignKey("resource_classes.id"))
    total = Column(Integer)
    reserved = Column(Integer)
    allocation_ratio = Column(Float)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255))


class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255))


class Consumer(Base):
    __tablename__ = 'consumers'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    user = orm.relationship(
        User,
        lazy='subquery',
        primaryjoin='User.id == Consumer.user_id')
    project = orm.relationship(
        Project,
        lazy='subquery',
        primaryjoin='Project.id == Consumer.project_id')


class Allocation(Base):
    __tablename__ = 'allocations'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    consumer_id = Column(Integer, ForeignKey("consumers.id"))
    resource_class_id = Column(Integer, ForeignKey("resource_classes.id"))
    resource_provider_id = Column(Integer, ForeignKey("resource_providers.id"))
    used = Column(Integer)

    consumer = orm.relationship(
        Consumer,
        lazy='subquery',
        primaryjoin='Consumer.id == Allocation.consumer_id')


class ResourceClass(Base):
    __tablename__ = 'resource_classes'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))


class ResourceProvider(Base):
    __tablename__ = 'resource_providers'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    name = Column(String(255))

    allocations = orm.relationship(
        Allocation,
        lazy='subquery',
        primaryjoin='ResourceProvider.id == Allocation.resource_provider_id')
    inventories = orm.relationship(
        Inventory,
        lazy='subquery',
        primaryjoin='ResourceProvider.id == Inventory.resource_provider_id')


class ResourceProviderAggregate(Base):
    __tablename__ = 'resource_provider_aggregates'
    __table_args__ = (
        table_args()
    )

    resource_provider_id = Column(Integer, ForeignKey("resource_providers.id"),
                                  primary_key=True)
    aggregate_id = Column(Integer, ForeignKey("placement_aggregates.id"))

    resource_providers = orm.relationship(
        ResourceProvider,
        lazy='subquery',
        primaryjoin='ResourceProvider.id == \
                     ResourceProviderAggregate.resource_provider_id')


class PlacementAggregate(Base):
    __tablename__ = 'placement_aggregates'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))

    rps = orm.relationship(
        ResourceProviderAggregate,
        lazy='subquery',
        primaryjoin='PlacementAggregate.id == \
                     ResourceProviderAggregate.aggregate_id')
