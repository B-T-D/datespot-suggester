import unittest
import json

from project_constants import *
import models
from database_api import DatabaseAPI


class TestHelloWorldThings(unittest.TestCase):

    # Todo very important to test hard cases. Huge cases, edge cases, corner cases--try to break it. 

    def setUp(self):

        # Blank out the test JSON files:
        data_map = { # todo DRY, this is repeated in every model interface's tests module
            "user_data": "test/testing_mockUserDB.json",
            "datespot_data": "test/testing_mockDatespotDB.json",
            "match_data": "test/testing_mockMatchData.json",
            "review_data": "test/testing_mockReviewData.json",
            "message_data": "test/testing_mockMessageData.json",
            "chat_data": "test/testing_mockChatData.json"
            }
        with open(TEST_JSON_DB_NAME, 'w') as fobj:
            json.dump(data_map, fobj)
            fobj.seek(0)

        # make sure all the test-mock JSONs exist
        for filename in data_map:
            with open(data_map[filename], 'w') as fobj:
                json.dump({}, fobj)
                fobj.seek(0)

        # Make a mock restaurant
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

        # Make mock text
        self.mock_text_positive_relevant = "This was a wonderful place to go on a date. I had the pasta. It was authentic and not from Pizza Hut."
        self.expected_sentiment = 0.1906 # todo hardcoded
        self.expected_relevance = round(1 / len(self.mock_text_positive_relevant), SENTIMENT_DECIMAL_PLACES) # i.e. "date" appears once.

        # Connect to the database with the mock data set
        self.db = DatabaseAPI(json_map_filename=TEST_JSON_DB_NAME)
        args_data = {"object_model_name": "datespot", "object_data": terrezanos_data}
        self.terrezanos_id = self.db.post_object(args_data)

        # Instantiate mock Review object

        self.review_obj = models.Review(datespot_id = self.terrezanos_id, text = self.mock_text_positive_relevant)

    def test_init(self):
        self.assertIsInstance(self.review_obj, models.Review)
    
    def test_tokenize(self):
        """Does the internal tokenize method tokenize a multi-sentence text into an array of sentences as expected?"""
        expected_sentences = [
            "This was a wonderful place to go on a date.",
            "I had the pasta.",
            "It was authentic and not from Pizza Hut."
        ]
        self.review_obj._tokenize()
        for i in range(len(expected_sentences)):
            self.assertEqual(expected_sentences[i], self.review_obj._sentences[i])

        # todo test the length of each
    
    def test_analyze_sentiment(self):
        self.review_obj._analyze_sentiment()
        self.assertAlmostEqual(self.expected_sentiment, self.review_obj._sentiment)
    
    def test_public_sentiment_attribute(self):
        """
        Can the sentiment be accessed as expected via the object's public sentiment attribute?
        """
        self.assertAlmostEqual(self.expected_sentiment, self.review_obj.sentiment)
    
    def test_analyze_relevance(self):
        self.review_obj._analyze_relevance()
        self.assertAlmostEqual(self.expected_relevance, self.review_obj._analyze_relevance())
    
    def test_public_relevance_attribute(self): # todo tbd if any external code ever needs this
        self.assertAlmostEqual(self.expected_relevance, self.review_obj.relevance)