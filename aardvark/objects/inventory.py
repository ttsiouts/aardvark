
import aardvark.conf

CONF = aardvark.conf.CONF

class Inventory(object):

    _attrs = ['allocation_ratio', 'used', 'reserved', 'max_unit', 'step_size',
              'min_unit', 'total']

    def __init__(self, resource_class, **kwargs):
        self.resource_class = resource_class
        for attr in self._attrs:
            try:
                setattr(self, attr, float(kwargs[attr]))
            except KeyError:
                setattr(self, attr, 0.0)

    @property
    def free(self):
        return self.total - (self.reserved + self.used)

    @property
    def usage(self):
        # NOTE(ttsiouts): multiply with 100 to avoid float for start...
        if self.total:
            return (self.reserved + self.used)*100/ self.total
        return 0

    @property
    def limit(self):
        return (self.total * CONF.aardvark.watermark) / 100

    @property
    def excessive(self):
        if self.usage <= CONF.aardvark.watermark:
            return 0
        else:
            return self.used + self.reserved - self.limit

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
        return "<Inventory: %s: total: %s , used: %s, usage: %s%%>" % (
            self.resource_class, self.total, self.used + self.reserved,
            self.usage)
