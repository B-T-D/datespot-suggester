import unittest
import json
import random

try:
    from python_backend.datespot_api import DatespotAPI
    from python_backend.datespot import Datespot
except:
    from datespot_api import DatespotAPI
    from datespot import Datespot

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
        assert self.terrezanos_id in self.api._data
        
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
        terrezanos_data = self.api._data[self.terrezanos_id]
        for key, expected_type in [("location", tuple), ("name", str), ("traits", list), ("price_range", int), ("hours", list)]:
            self.assertIsInstance(terrezanos_data[key], expected_type)
    
    def test_update_datespot_traits(self):
        """Are traits updates written to the stored JSON file as expected?"""
        new_terrezanos_trait = "not at a Terrezano's"
        # update with a single string:
        self.api.update_datespot(self.terrezanos_id, traits=new_terrezanos_trait)
        self.assertIn(new_terrezanos_trait, self.api._data[self.terrezanos_id]["traits"]) # self.api._data[myKey] isn't correct way to query it from the outside. External caller can't expect the object instance to persist.

        # update with a list:
        # todo

class TestQueriesOnPersistentDB(unittest.TestCase):
    """Tests using a persistent "real" DB rather than a separate DB initialized solely for testing purposes."""

    def setUp(self):
        self.api = DatespotAPI() # let it use the default DB file
        self.test_location = (40.74491605331198, -74.00333467806617)
        self.test_radius = 2000

        self.expected_datespot_data_keys = ["id", "location", "name", "traits", "price_range", "hours"]
    
    def test_init(self):
        self.assertIsInstance(self.api, DatespotAPI)
    
    def test_api_has_data(self):
        self.assertGreater(self.api.query_num_datespots(), 0)
        self.assertEqual(self.api.query_num_datespots(), 60) # todo hardcoded to 60 for expediency
    
    def test_api_data_has_expected_shape(self):
        data = self.api.get_all_data()
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
        for key in data:
            self.assertIsInstance(key, int) # keys should be ints
            datespot_dict = data[key]
            for schema_key in self.expected_datespot_data_keys:
                self.assertIn(schema_key, datespot_dict)
    
    def test_query_datespots_near_return_type(self):
        returned_obj = self.api.query_datespots_near(location=self.test_location, radius=self.test_radius)
        self.assertIsInstance(returned_obj, list)

    def test_query_datespots_near_returns_locations_within_radius(self):
        """Is the distance between the test location each query result <= the query radius?"""
        query_results = self.api.query_datespots_near(location=self.test_location, radius=self.test_radius)
        # print(f"\n------------------------------------")
        # for result in query_results:
        #     print(f"{result[0]}\t|\t{result[1]}")
        # print(f"------------------------------------\n")
        for result in query_results:
            distance = result[0]
            self.assertLessEqual(distance, self.test_radius)
    
    def test_query_datespots_returns_nonincreasing_values(self):
        """Are the elements in the query result non-increasing, i.e. sorted nearest to farthest?"""
        query_results = self.api.query_datespots_near(location=self.test_location, radius=self.test_radius)

        for i in range(1, len(query_results)):
            self.assertGreaterEqual(query_results[i], query_results[i-1])

    # todo robust, general case test confirming that the distances are correct. 

if __name__ == '__main__':
    unittest.main() # todo the other ones need this for unittest to run them without pytest.