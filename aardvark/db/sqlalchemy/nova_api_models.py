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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer
from sqlalchemy.types import TEXT

import aardvark.conf


CONF = aardvark.conf.CONF


def table_args():
    engine_name = 'mysql'
    if engine_name == 'mysql':
        return {'mysql_engine': CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


Base = declarative_base()


class CellMapping(Base):
    __tablename__ = 'cell_mappings'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    name = Column(String(255))
    database_connection = Column(TEXT)
    disabled = Column(Boolean)


class Aggregate(Base):
    __tablename__ = 'aggregates'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    name = Column(String(255))
