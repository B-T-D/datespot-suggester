import unittest
import json
import random

import models

try:
    from python_backend.model_interfaces import DatespotModelInterface
    from python_backend.datespot import Datespot
except:
    from model_interfaces import DatespotModelInterface

# todo, style--define global constants before or after imports?

DATESPOT_ID_TYPE = str
TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"


class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):

        dataMap = { # todo DRY, this is repeated in every model interface's tests module
            "user_data": "test/testing_mockUserDB.json",
            "datespot_data": "test/testing_mockDatespotDB.json",
            "match_data": "test/testing_mockMatchData.json",
            "review_data": "test/testing_mockReviewData.json"
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
        self.api = DatespotModelInterface(json_map_filename = TEST_JSON_DB_NAME)

        # make a mock restaurant
        self.terrezanos_location = (40.72289821341384, -73.97993915779077)
        self.terrezanos_name = "Terrezano's"
        self.terrezanos_traits = {
            "italian": [1.0, "discrete"],
            "wine": [0.5, 1],
            "pasta": [0.6, 2],
            "NOT FROM PIZZA HUT": [0.01, 2],
            "authentic": [-0.05, 3],
            "warehouse": [1.0, "discrete"]
            }
        self.terrezanos_price_range = 2
        self.terrezanos_hours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now

        self.terrezanos_data = {
                "location" : self.terrezanos_location,
                "name" : self.terrezanos_name,
                "traits" : self.terrezanos_traits,
                "price_range" : self.terrezanos_price_range,
                "hours" : self.terrezanos_hours,
            }

        self.terrezanos_id = self.api.create(self.terrezanos_data)
        assert self.terrezanos_id in self.api._data
        
    def test_instantiation(self):
        self.assertIsInstance(self.api, DatespotModelInterface)
    
    def test_create_datespot(self):
        domenicos_location = (40.723889184134926, -73.97613846772394)
        domenicos_name = "Domenico's"
        domenicos_traits = {
            "coffee": [1.0, 1], # todo...So we're imagining this as ~ how good the coffee is, rather than the discrete fact that they do serve coffee?
            "coffee shop": [1.0, "discrete"],
            "gourmet": [0.25, 1],
            "americano": [0.15, 1],
            "knows coffee": [0.3, 1],
            "bricks": [0.6, 1],
            "burger juice": [0.9, 1]
        }
        domenicos_price_range = 1
        domenicos_hours = [[8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [10, 17]]

        domenicos_data = {
            "location" : domenicos_location,
            "name" : domenicos_name,
            "traits" : domenicos_traits,
            "price_range" : domenicos_price_range,
            "hours" : domenicos_hours
        }

        domenicos_key = self.api.create(domenicos_data)
        self.assertIsInstance(domenicos_key, DATESPOT_ID_TYPE)
        domenicos = self.api.lookup_obj(domenicos_key)
        self.assertEqual(str(type(domenicos)), "DatespotObj")
    
    def test_native_python_dict_value_types(self):
        """Are the values in the API's native python dictionary stored as the intended types, rather than as strings?"""
        terrezanos_data = self.api._data[self.terrezanos_id]
        for key, expected_type in [("location", tuple), ("name", str), ("traits", dict), ("price_range", int), ("hours", list)]:
            self.assertIsInstance(terrezanos_data[key], expected_type)
    
    def test_update_datespot_traits(self):
        """Are traits updates written to the stored JSON file as expected?"""
        new_terrezanos_trait = "not at a Terrezano's"
        # update with a single string:
        update_data = {
            "traits": {"not at a Terrezano's": [0.95, 1]}
        }

        self.api.update(self.terrezanos_id, update_data=update_data)
        updated_obj = self.api.lookup_obj(self.terrezanos_id)
        self.assertIn(new_terrezanos_trait, updated_obj.traits) # self.api._data[myKey] isn't correct way to query it from the outside. External caller can't expect the object instance to persist.
        # update with a list:
        # todo
    
    def test_is_in_db(self):
        """Does the method that checks if an ID is already in the database behave as expected?"""
        self.assertTrue(self.api.is_in_db(self.terrezanos_data)) # JSON for the same restaurant should hash to same thing
        # Todo add an assertFalse

class TestQueriesOnPersistentDB(unittest.TestCase):
    """Tests using a persistent "real" DB rather than a separate DB initialized solely for testing purposes."""

    def setUp(self):
        self.api = DatespotModelInterface() # let it use the default DB file
        self.test_location = (40.74491605331198, -74.00333467806617)
        self.test_radius = 2000

        self.expected_datespot_data_keys = ["location", "name", "traits", "price_range", "hours", "yelp_rating", "yelp_review_count", "yelp_url"]
    
    def test_init(self):
        self.assertIsInstance(self.api, DatespotModelInterface)
    
    def test_api_has_data(self):
        self.assertGreater(self.api.query_num_datespots(), 0)
        self.assertEqual(self.api.query_num_datespots(), 50) # todo hardcoded to 50 (i.e. max from one yelp request)
    
    def test_api_data_has_expected_shape(self):
        data = self.api._get_all_data()
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
        for key in data:
            self.assertIsInstance(key, DATESPOT_ID_TYPE) # keys should be ints
            datespot_dict = data[key]
            for schema_key in self.expected_datespot_data_keys:
                self.assertIn(schema_key, datespot_dict)
    
    def test_query_datespot_ids_near_return_type(self):
        returned_obj = self.api.query_datespot_ids_near(location=self.test_location, radius=self.test_radius)
        self.assertIsInstance(returned_obj, list)

    def test_query_datespot_ids_near_near_returns_locations_within_radius(self):
        """Is the distance between the test location each query result <= the query radius?"""
        query_results = self.api.query_datespot_ids_near(location=self.test_location, radius=self.test_radius)
        for result in query_results:
            distance = result[0]
            self.assertLessEqual(distance, self.test_radius)
    
    def test_query_datespot_ids_near_returns_nonincreasing_values(self):
        """Are the elements in the query result non-increasing, i.e. sorted nearest to farthest?"""
        query_results = self.api.query_datespot_ids_near(location=self.test_location, radius=self.test_radius)

        for i in range(1, len(query_results)):
            self.assertGreaterEqual(query_results[i], query_results[i-1])

    # todo robust, general case test confirming that the distances are correct. 

if __name__ == '__main__':
    unittest.main() # todo the other ones need this for unittest to run them without pytest.