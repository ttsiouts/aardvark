from  aardvark.api.rest import placement
from oslotest import base


class PlacementTests(base.BaseTestCase):

    def setUp(self):
        super(PlacementTests, self).setUp()
        self.client = placement.PlacementClient()

    def test_basic(self):
        pass
