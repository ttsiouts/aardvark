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


from aardvark.objects.nova import cell_mapping

CELL_MAPPINGS = dict()


def get_cell_connection(cell_name):
    global CELL_MAPPINGS
    try:
        return CELL_MAPPINGS[cell_name]
    except KeyError:
        CELL_MAPPINGS = {
            cm.name: cm for cm in cell_mapping.CellMapping.list_cell_mappings()
        }
        return CELL_MAPPINGS[cell_name].database_connection
