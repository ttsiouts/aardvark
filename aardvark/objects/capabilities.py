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

from aardvark.objects import inventory 
from aardvark.objects import resources 


class Capabilities(object):
    """Representation of the capabilities of a resource_provider

    Just a helper class that enables the reaper to make simple calculations
    with resources.
    """

    def __init__(self, inventories=None):
        self.inventories = inventories

    @staticmethod
    def obj_from_primitive(primitive, usage=None):
        inventories = dict()
        for rc, kwargs in primitive.items():
            if usage:
                # NOTE(ttsiouts): If usage is provided add also the used
                kwargs.update({
                    'used': usage[rc],
                })
            inventories.update({rc: inventory.Inventory(rc, **kwargs)})
        return Capabilities(inventories)

    @staticmethod
    def obj_from_resources(resources):
        inventories = dict()
        for rc, value in resources.to_dict().items():
            if value < 0:
                inventories.update({rc: inventory.Inventory(rc, used=value)})
            else:
                inventories.update({rc: inventory.Inventory(rc, total=value)})
        return Capabilities(inventories)

    @property
    def resource_classes(self):
        return set([inv.resource_class for _, inv in self.inventories.items()])

    @property
    def free_resources(self):
        free = {rc: inv.free for rc, inv in self.inventories.items()}
        return resources.Resources(free)

    def __add__(self, other):
        resource_classes = self.resource_classes | other.resource_classes
        new = dict()
        for rc in resource_classes:
            new.update({
                rc: self.inventories.get(rc, inventory.Inventory(rc))  + self.inventories.get(rc, inventory.Inventory(rc))})
        return Capabilities(new)

    def get_excessive_resources(self):
        request = {rc: inv.excessive for rc, inv in self.inventories.items()
                   if inv.excessive != 0}
        return resources.Resources(request)
        
    #def __sub__(self, other):
    #    resources = self.resources | other.resources
    #    new = dict()
    #    for res in resources:
    #        value = getattr(self, res, 0) - getattr(other, res, 0)
    #        new[res] = int(value)
    #    return Resources(new)

    #def __mul__(self, other):
    #    # NOTE(ttsiouts): Should be used only with numbers... Resource * 3
    #    new = dict()
    #    for res in self.resources:
    #        try:
    #            new[res] = int(getattr(self, res, 0) * other)
    #        except TypeError:
    #            return None
    #    return Resources(new)

    #def __truediv__(self, other):
    #    # NOTE(ttsiouts): the result of this operation is the minimum result
    #    # after dividing all the resource classes:
    #    # e.g. a = {vcpu: 100, memory: 1024}, b = {vcpu: 1, memory: 512}
    #    #      a / b = 2 (because a.memory / b.memory = 2)
    #    result = -1
    #    for resource in other.resources:
    #        if getattr(self, resource, 0) < getattr(other, resource, 0):
    #            res = 0
    #        else:
    #            # NOTE: Careful with the default values of getattr!
    #            # division with zero :P
    #            res = getattr(self, resource, 0) / getattr(other, resource, 1)
    #        if result == -1 or res < result:
    #            result = res
    #    return int(result)

    #def __div__(self, other):
    #    # NOTE(ttsiouts): the result of this operation is the minimum result
    #    # after dividing all the resource classes:
    #    # e.g. a = {vcpu: 100, memory: 1024}, b = {vcpu: 1, memory: 512}
    #    #      a / b = 2 (because a.memory / b.memory = 2)
    #    result = -1
    #    for resource in other.resources:
    #        if getattr(self, resource, 0) < getattr(other, resource, 0):
    #            res = 0
    #        else:
    #            # NOTE: Careful with the default values of getattr!
    #            # division with zero :P
    #            res = getattr(self, resource, 0) / getattr(other, resource, 1)
    #        if result == -1 or res < result:
    #            result = res
    #    return int(result)

    #def __eq__(self, other):
    #    resources = self.resources | other.resources
    #    for res in resources:
    #        if getattr(self, res, 0) != getattr(other, res, 0):
    #            return False
    #    return True

    #def __ne__(self, other):
    #    return not self == other

    def __gt__(self, other):
        return any(inv.usage > other for _,inv in self.inventories.items())

    #def __lt__(self, other):
    #    resp = True
    #    for res in self.resources:
    #        resp = resp and getattr(self, res) < getattr(other, res, 0)
    #    return resp

    #def __ge__(self, other):
    #    resp = True
    #    for res in self.resources:
    #        resp = resp and getattr(self, res) >= getattr(other, res, 0)
    #    return resp

    #def __le__(self, other):
    #    resp = True
    #    for res in self.resources:
    #        resp = resp and getattr(self, res) <= getattr(other, res, 0)
    #    return resp

    def __repr__(self):
        text = ', '.join([inv.to_str() for _,inv in self.inventories.items()])
        return '<Capabilities(%s)>' % text

    #def to_dict(self):
    #    tdict = dict()
    #    for resource in self.resources:
    #        tdict.update({resource: getattr(self, resource)})
    #    return tdict

