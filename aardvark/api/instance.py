from aardvark.api.rest import nova
from aardvark.objects import instance

class Instance(object):

    def __init__(self, uuid, name, flavor):
        self.uuid = uuid
        self.name = name
        self.flavor = flavor


class InstanceList(object):

    def __init__(self):
        self.client = nova.novaclient()

    def instances(self, **filters):
        if 'project_id' in filters:
            filters.update({'all_tenants': True})
        return [instance.Instance(server.id, server.name, server.flavor)
                for server in self.client.servers.list(search_opts=filters)]

    def delete_instance(self, instance):
        self.client.servers.delete(instance.uuid)
