from aardvark.objects import base
from aardvark.objects import resources

class Instance(base.BaseObjectWrapper):

    _attrs = ['name', 'uuid', 'flavor']

    def __init__(self, uuid, name, flavor):
        super(Instance, self).__init__(uuid, name, flavor)
        self.uuid = uuid
        self.name = name
        self.flavor = flavor

    @property
    def resources(self):
        return resources.Resources.obj_from_flavor(self.flavor)


class InstanceList(base.BaseObjectWrapper):

    _attrs = ['instances']

    def __init__(self):
        super(InstanceList, self).__init__()

    def instances(self, **filters):
        instances =  self._resource.instances(**filters)
        return instances

    def delete_instance(self, instance):
        self._resource.delete_instance(instance)
