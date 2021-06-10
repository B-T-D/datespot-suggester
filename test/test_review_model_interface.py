import unittest
import json

from model_interfaces import ReviewModelInterface, DatespotModelInterface

from database_api import DatabaseAPI

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"

class TestHelloWorldThings(unittest.TestCase):
    """Simple non-brokenness tests."""

    def setUp(self):

        data_map = { # todo DRY, this is repeated in every model interface's tests module
            "user_data": "test/testing_mockUserDB.json",
            "datespot_data": "test/testing_mockDatespotDB.json",
            "match_data": "test/testing_mockMatchData.json",
            "review_data": "test/testing_mockReviewData.json"
            }

        with open(TEST_JSON_DB_NAME, 'w') as fobj:
            json.dump(data_map, fobj)
            fobj.seek(0)

        # make sure all the test-mock JSONs exist
        for filename in data_map:
            with open(data_map[filename], 'w') as fobj:
                json.dump({}, fobj)
                fobj.seek(0)

        self.api = ReviewModelInterface(json_map_filename = TEST_JSON_DB_NAME)
        self.datespot_api = DatespotModelInterface(json_map_filename = TEST_JSON_DB_NAME)

        # Make mock restaurant
        self.terrezanos_location = (40.72289821341384, -73.97993915779077)
        self.terrezanos_name = "Terrezano's"
        self.terrezanos_traits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
        self.terrezanos_price_range = 2
        self.terrezanos_hours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now

        terrezanos_data = {
            "location" : self.terrezanos_location,
            "name" : self.terrezanos_name,
            "traits" : self.terrezanos_traits,
            "price_range" : self.terrezanos_price_range,
            "hours" : self.terrezanos_hours,
        }
        
        self.db = DatabaseAPI(json_map_filename=TEST_JSON_DB_NAME)
        self.terrezanos_id = self.datespot_api.create(terrezanos_data)

        # Make mock text
        self.mock_text_positive_relevant = "This was a wonderful place to go on a date. I had the pasta. It was authentic and not from Pizza Hut."
        self.expected_sentiment = 0.1906 # todo hardcoded
        self.expected_relevance = round(1 / len(self.mock_text_positive_relevant), 4) # i.e. "date" appears once.
    
    def test_instantiation(self):
        self.assertIsInstance(self.api, ReviewModelInterface)
    
    def test_create(self):
        review_data = {
            "datespot_id": self.terrezanos_id,
            "text": self.mock_text_positive_relevant
        }
        review_id = self.api.create(review_data)
        self.assertIn(review_id, self.api._data)
        