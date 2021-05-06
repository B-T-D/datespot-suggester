import unittest
import json

from python_backend.datespot_api import DatespotAPI
from python_backend.datespot import Datespot

TEST_JSON_DB_NAME = "test/mock_datespot_data.json"

data = {}
with open(TEST_JSON_DB_NAME, 'w') as fobj:
    json.dump(data, fobj)
    fobj.seek(0)
fobj.close()

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):
        # create a fake DB
        self.api = DatespotAPI(datafile_name = "test/mock_datespot_data.json")

        # make a mock restaurant
        self.cached_location_key = (40.72289821341384, -73.97993915779077, 0) # location_key[2] is a vertical coordinate for resolving hypothetically possible (x, y) collisions
        assert type(self.cached_location_key) == tuple
        terrezanosTraits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
        terrezanosHours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now
        self.mockRestaurant = Datespot(
            location = self.cached_location_key,
            name = "Terrezano's",
            traits = terrezanosTraits,
            price_range = 2,
            hours = terrezanosHours
            )
    
    def test_instantiation(self):
        self.assertIsInstance(self.mockRestaurant, Datespot)



40.72289821341384, -73.97993915779077
        