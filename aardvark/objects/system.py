from aardvark.objects import base
from aardvark.objects import resource_provider
from aardvark.objects import project

class System(object):

    def __init__(self):
        self._rp_list = resource_provider.ResourceProviderList()
        self._project_list = project.ProjectList()

    @property
    def resource_providers(self):
        return self._rp_list.resource_providers

    @property
    def projects(self):
        return self._project_list.projects

    @property
    def preemptible_projects(self):
        return self._project_list.preemptible_projects

    def usage(self):
        total_cap = None
        for rp in self.resource_providers:
            if total_cap is None:
                total_cap = rp.capabilities
            else:
                total_cap += rp.capabilities
            rp.reinit_object()
        return total_cap

    def empty_cache(self):
        self._rp_list.reinit_object()
        self._project_list.reinit_object()
