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

import aardvark.conf

CONF = aardvark.conf.CONF

class Inventory(object):

    _attrs = ['allocation_ratio', 'used', 'reserved', 'max_unit', 'step_size',
              'min_unit', 'total']

    def __init__(self, resource_class, **kwargs):
        self.resource_class = resource_class
        for attr in self._attrs:
            try:
                setattr(self, attr, kwargs[attr])
            except KeyError:
                setattr(self, attr, 0)

    @property
    def free(self):
        return self.total - (self.reserved + self.used)

    @property
    def percentage(self):
        # NOTE(ttsiouts): multiply with 100 to avoid float for start...
        return (self.reserved + self.used)*100/ self.total

    @property
    def limit(self):
        #return self.total * (CONF.aardvark.watermak / 100)
        return self.total * (75 / 100)

    def __add__(self, other):
        kwargs = {
            'used': self.used + other.used,
            'reserved': self.reserved + other.reserved,
            'total': self.total + other.total,
        }
        return Inventory(self.resource_class, **kwargs)

    def __repr__(self):
        return self.to_str()

    def to_str(self):
        return "<Inventory: %s: total: %s , used: %s, reserved: %s, usage: %s%%>" % (
            self.resource_class, self.total, self.used, self.reserved, self.percentage)
