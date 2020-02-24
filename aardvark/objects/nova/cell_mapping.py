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

from aardvark.db import nova_api as dbapi
from aardvark.objects import base


class CellMapping(base.NovaLoadedObject):

    dbapi = dbapi.get_instance()

    def __init__(self, id, uuid, name, database_connection):
        self.id = id
        self.uuid = uuid
        self.name = name
        self.database_connection = database_connection

    @staticmethod
    def from_db_object(db_object):
        return CellMapping(db_object.id, db_object.uuid, db_object.name,
                           db_object.database_connection)

    @staticmethod
    def list_cell_mappings():
        db_objects = CellMapping.dbapi.list_cell_mappings()
        return [
            CellMapping.from_db_object(obj) for obj in db_objects
        ]

    @staticmethod
    def get_cell_mappings_from_aggregates(aggregates):
        db_objects = CellMapping.dbapi.cell_mappings_from_aggregates(
            aggregates)
        return [
            CellMapping.from_db_object(obj) for obj in db_objects
        ]
