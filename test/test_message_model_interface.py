import unittest
import json
import time

from model_interfaces import MessageModelInterface
from database_api import DatabaseAPI

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json" # todo if all these tests were in a single module like the MIs are, could just define
                                                    #   these constants once at top of that huge module. 

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):

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

        # make sure all the test-mock JSONs exist:
        for filename in data_map:
            with open(data_map[filename], 'w') as fobj:
                json.dump({}, fobj)
                fobj.seek(0)
        
        # Instantiate model interface and DB connection:
        self.api = MessageModelInterface(json_map_filename = TEST_JSON_DB_NAME)
        self.db = DatabaseAPI(json_map_filename = TEST_JSON_DB_NAME)

        # Make three mock users

        self.akatosh_name = "Akatosh"
        self.akatosh_location = (40.73517750328247, -74.00683227856715)
        self.akatosh_id = "1"
        akatosh_json = json.dumps({
            "name": self.akatosh_name,
            "current_location": self.akatosh_location,
            "force_key": self.akatosh_id
        })
        self.db.post_object("user", akatosh_json) # Don't need to store the key returned by this, forced it to "1"

        self.stendarr_name = "Stendarr"
        self.stendarr_location = (40.74769591216627, -73.99447266003756)
        self.stendarr_id = "2"
        stendarr_json = json.dumps({
            "name": self.stendarr_name,
            "current_location": self.stendarr_location,
            "force_key": self.stendarr_id
        })
        self.db.post_object("user", stendarr_json)

        self.talos_name = "Talos"
        self.talos_location = (40.76346250260515, -73.98013893542904)
        self.talos_id = "3"
        talos_json = json.dumps({
            "name": self.talos_name,
            "current_location": self.talos_location,
            "force_key": self.talos_id
        })
        self.db.post_object("user", talos_json)

        # Mock message data:

        self.mock_bilateral_timestamp = time.time()
        self.quick_mock_chat_json = json.dumps({
            "start_time": time.time(),
            "participant_ids": [self.akatosh_id, self.stendarr_id]
        })
        self.mock_chat_id_1 = self.db.post_object("chat", self.quick_mock_chat_json)
        self.single_sentence_text = "Worship the Nine, do your duty, and heed the commands of the saints and priests."
        self.expected_sentiment_single_sentence = 0.296 # todo hardcoded
    
    def test_instantiation(self):
        self.assertIsInstance(self.api, MessageModelInterface)
    
    def test_create_message(self):
        json_str = json.dumps({
            "time_sent": self.mock_bilateral_timestamp,
            "sender_id": self.akatosh_id,
            "chat_id": self.mock_chat_id_1,
            "text": self.single_sentence_text
        })
        message_id = self.api.create_message(json_str)
        self.assertIn(message_id, self.api._data)
