import unittest
import json
import random

from python_backend.datespot_api import DatespotAPI
from python_backend.datespot import Datespot

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"


class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):

        dataMap = {
            "user_data": "test/testing_mockUserDB.json",
            "datespot_data": "test/testing_mockDatespotDB.json",
            "match_data": "test/testing_mockMatchData.json"
            }
        with open(TEST_JSON_DB_NAME, 'w') as fobj:
            json.dump(dataMap, fobj)
            fobj.seek(0)

        # make sure all the test-mock JSONs exist
        for filename in dataMap:
            with open(dataMap[filename], 'w') as fobj:
                json.dump({}, fobj)
                fobj.seek(0)

        # create a fake DB
        self.api = DatespotAPI(datafile_name = TEST_JSON_DB_NAME)

        # make a mock restaurant
        self.cached_location_key = (40.72289821341384, -73.97993915779077, 0.0) # location_key[2] is a vertical coordinate for resolving hypothetically possible (x, y) collisions
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
        
        self.terrezanos_location = (40.72289821341384, -73.97993915779077)
        self.terrezanos_name = "Terrezano's"
        self.terrezanos_traits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
        self.terrezanos_price_range = 2
        self.terrezanos_hours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now
        """
        self.terrezanos_id = self.api.create_datespot(
            location = self.terrezanos_location,
            name = self.terrezanos_name,
            traits = self.terrezanos_traits,
            price_range = self.terrezanos_price_range,
            hours = self.terrezanos_hours,
        )
        """
        self.terrezanos_id = self.api.create_datespot(
            json.dumps({
                "location" : self.terrezanos_location,
                "name" : self.terrezanos_name,
                "traits" : self.terrezanos_traits,
                "price_range" : self.terrezanos_price_range,
                "hours" : self.terrezanos_hours,
            })
        )
        assert self.terrezanos_id in self.api.data
        
    def test_instantiation(self):
        self.assertIsInstance(self.api, DatespotAPI)
    
    def test_create_datespot(self):
        domenicos_location = (40.723889184134926, -73.97613846772394)
        domenicos_name = "Domenico's"
        domenicos_traits = ["coffee", "coffee shop", "gourmet", "americano", "knows coffee", "bricks", "burger juice"]
        domenicos_price_range = 1
        domenicos_hours = [[8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [10, 17]]

        domenicos_json = json.dumps({
            "location" : domenicos_location,
            "name" : domenicos_name,
            "traits" : domenicos_traits,
            "price_range" : domenicos_price_range,
            "hours" : domenicos_hours
        })

        domenicos_key = self.api.create_datespot(domenicos_json)
        self.assertIsInstance(domenicos_key, int)
        domenicos = self.api.lookup_datespot(domenicos_key)
        self.assertEqual(str(type(domenicos)), "DatespotObj")
    
    def test_native_python_dict_value_types(self):
        """Are the values in the API's native python dictionary stored as the intended types, rather than as strings?"""
        terrezanos_data = self.api.data[self.terrezanos_id]
        for key, expected_type in [("location", tuple), ("name", str), ("traits", list), ("price_range", int), ("hours", list)]:
            self.assertIsInstance(terrezanos_data[key], expected_type)

if __name__ == '__main__':
    unittest.main() # todo the other ones need this for unittest to run them without pytest.