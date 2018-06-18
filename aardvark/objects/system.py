from aardvark.objects import base

class System(base.PlacementObjectWrapper):

    _attrs = ['resource_classes', 'resource_providers', 'traits']

    def __init__(self):
        super(System, self).__init__()

    def state(self):
        total_cap = None
        for rp in self.resource_providers:
            if total_cap is None:
                total_cap = rp.capabilities
            else:
                total_cap += rp.capabilities
            rp.reinit_object()
        return total_cap

    def reinit_cache(self):
        for rp in self.resource_providers:
            rp.reinit_object()
