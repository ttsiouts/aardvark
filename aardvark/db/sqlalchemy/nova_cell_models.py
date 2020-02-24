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
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
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


class ResourceProvider(Base):
    __tablename__ = 'compute_nodes'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    hypervisor_hostname = Column(String(255))
    vcpus = Column(Integer)
    memory_mb = Column(Integer)
    local_gb = Column(Integer)
    vcpus_used = Column(Integer)
    memory_mb_used = Column(Integer)
    local_gb_used = Column(Integer)
    free_ram_mb = Column(Integer)
    free_disk_gb = Column(Integer)
    deleted = Column(Integer)
    ram_allocation_ratio = Column(Float)
    cpu_allocation_ratio = Column(Float)
    disk_allocation_ratio = Column(Float)
    disk_available_least = Column(Integer)


class InstanceMeta(Base):
    __tablename__ = 'instance_metadata'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_uuid = Column(String(36), ForeignKey("instances.uuid"))
    key = Column(String(255))
    value = Column(String(255))


class Instance(Base):
    __tablename__ = 'instances'
    __table_args__ = (
        table_args()
    )

    created_at = Column(DateTime)
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    hostname = Column(String(255))
    deleted = Column(Boolean)
    host = Column(String(255))
    vcpus = Column(Integer)
    memory_mb = Column(Integer)
    root_gb = Column(Integer)
    ephemeral_gb = Column(Integer)
    user_id = Column(String(255))
    project_id = Column(String(255))
    image_ref = Column(String(255))
    instance_type_id = Column(Integer)
    meta = orm.relationship(
        InstanceMeta,
        lazy='subquery',
        primaryjoin='Instance.uuid == InstanceMeta.instance_uuid')
