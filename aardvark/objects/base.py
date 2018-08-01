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

from oslo_utils import importutils

import aardvark.conf


CONF = aardvark.conf.CONF


class BaseObjectWrapper(object):
    """Base class for objects from Other services"""

    _attrs = []
    _resource = None

    def __init__(self, *args, **kwargs):
        backend = "aardvark.api"
        module = importutils.try_import(backend)

        class_ = getattr(module, self.__class__.__name__)
        # NOTE(ttsiouts): this is the backend resource where the object's info
        # are loaded from.
        self._resource = class_(*args, **kwargs)

    def __getattribute__(self, attr):
        # NOTE(ttsiouts): if the attribute is not set, load it from the
        # backend, set it and finally return it.
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._attrs:
                raise
            value = getattr(self._resource, attr)
            setattr(self, attr, value)
            return value

    def reinit_object(self):
        for attr in self._attrs:
            if hasattr(self, attr):
                delattr(self, attr)

    def __repr__(self):
        to_string = ", ".join("%s = %s" % (attr, getattr(self, attr))
                              for attr in self._attrs if hasattr(self, attr))
        return "<%s: %s>" % (self.__class__.__name__, to_string)

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self, key, None)
        return obj


class PlacementObjectWrapper(BaseObjectWrapper):
    """Base class for Placement Objects

    We want to support both API and direct DB access in the case of Placement.
    This is why we have to dynamically load the backend depending on the
    configuration option that the operator chose.
    """

    def __init__(self, **kwargs):
        placement_backend = "aardvark.%s" % CONF.placement.backend
        module = importutils.try_import(placement_backend)

        class_ = getattr(module, self.__class__.__name__)
        # NOTE(ttsiouts): this is the backend resource where the object's info
        # are loaded from.
        self._resource = class_(**kwargs)
