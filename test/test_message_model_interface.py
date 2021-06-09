import unittest
import json
import time

from model_interfaces import MessageModelInterface, UserModelInterface, ChatModelInterface
from database_api import DatabaseAPI

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json" # todo if all these tests were in a single module like the MIs are, could just define
                                                    #   these constants once at top of that huge module. 

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):

        # Todo: Import subprocess and run the preprocess tastes script to sort the text file
        #   That doesn't need to be in setUp though, just once per time the tests are run. Maybe the shell script should do it.

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
        self.user_api = UserModelInterface(json_map_filename = TEST_JSON_DB_NAME)
        self.chat_api = ChatModelInterface(json_map_filename = TEST_JSON_DB_NAME)
        self.db = DatabaseAPI(json_map_filename = TEST_JSON_DB_NAME)


        # Make three mock users

        self.akatosh_name = "Akatosh"
        self.akatosh_location = (40.73517750328247, -74.00683227856715)
        self.akatosh_id = "1"
        akatosh_data = {
            "name": self.akatosh_name,
            "current_location": self.akatosh_location,
            "force_key": self.akatosh_id
        }
        self.user_api.create(akatosh_data)

        self.stendarr_name = "Stendarr"
        self.stendarr_location = (40.74769591216627, -73.99447266003756)
        self.stendarr_id = "2"
        stendarr_data = {
            "name": self.stendarr_name,
            "current_location": self.stendarr_location,
            "force_key": self.stendarr_id
        }
        self.user_api.create(stendarr_data)

        self.talos_name = "Talos"
        self.talos_location = (40.76346250260515, -73.98013893542904)
        self.talos_id = "3"
        talos_data = {
            "name": self.talos_name,
            "current_location": self.talos_location,
            "force_key": self.talos_id
        }
        self.user_api.create(talos_data)

        # Mock message data:

        self.mock_bilateral_timestamp = time.time()
        self.quick_mock_chat_data = {
            "start_time": time.time(),
            "participant_ids": [self.akatosh_id, self.stendarr_id]
        }
        self.mock_chat_id_1 = self.chat_api.create(self.quick_mock_chat_data)
        self.single_sentence_text = "Worship the Nine, do your duty, and heed the commands of the saints and priests."
        self.expected_sentiment_single_sentence = 0.296 # todo hardcoded

        # Mock message where user expresses tastes info

        self.tastes_message_timestamp = time.time()
        self.akatosh_taste_name = "italian"
        self.tastes_message_text = f"I love {self.akatosh_taste_name} food"
        self.expected_sentiment_tastes_sentence = 0.6369 # todo hardcoded
            # Todo import the identical sentiment analyzer here, and run it on the sentence, and save the result.
        self.tastes_message_data = {
            "time_sent": self.tastes_message_timestamp,
            "sender_id": self.akatosh_id,
            "chat_id": self.mock_chat_id_1,
            "text": self.tastes_message_text
        }
        self.tastes_message_id = self.api.create(self.tastes_message_data)

        # Mock message with negative taste sentiment
        self.negative_tastes_message_timestamp = time.time()
        self.akatosh_negative_taste_name = "thai"
        self.negative_tastes_message_text = f"I don't really like {self.akatosh_negative_taste_name} food"
        self.expected_sentiment_negative_tastes_sentence = -0.3241 # todo hardcoded
        self.negative_tastes_message_data = {
            "time_sent": self.negative_tastes_message_timestamp,
            "sender_id": self.akatosh_id,
            "chat_id": self.mock_chat_id_1,
            "text": self.negative_tastes_message_text
        }
        self.negative_tastes_message_id = self.api.create(self.negative_tastes_message_data)
    
    def test_instantiation(self):
        self.assertIsInstance(self.api, MessageModelInterface)
    
    def test_create(self):
        data = {
            "time_sent": self.mock_bilateral_timestamp,
            "sender_id": self.akatosh_id,  # MI is called with sender_id. MI then has sole responsibility for translating the MI to a user object literal.
            "chat_id": self.mock_chat_id_1,
            "text": self.single_sentence_text
        }
        message_id = self.api.create(data)
        self.assertIn(message_id, self.api._data)
    
    def test_tastes_updated_in_user_obj(self):
        positive_expected_taste_strength = self.expected_sentiment_tastes_sentence
        akatosh_obj = self.db.get_object("user", self.akatosh_id)
        positive_actual_taste_strength = akatosh_obj.taste_strength(self.akatosh_taste_name)
        self.assertAlmostEqual(positive_expected_taste_strength, positive_actual_taste_strength)

        # Test negative sentiment on new trait
        negative_expected_taste_strength = self.expected_sentiment_negative_tastes_sentence
        negative_actual_taste_strength = akatosh_obj.taste_strength(self.akatosh_negative_taste_name)
        self.assertAlmostEqual(negative_expected_taste_strength, negative_actual_taste_strength)

    def test_existing_taste_updated_in_user_obj(self):
        """Do the various methods behave as expectexd in adding a new sentiment datapoint to a previously known user taste?"""
        # Mock message with additional datapoint on a known taste
        self.second_datapoint_tastes_message_timestamp = time.time()
        self.second_datapoint_tastes_message_text = f"{self.akatosh_taste_name} is my favorite type of food"
        self.expected_sentiment_after_second_datapoint = 0.54785 # todo hardcoded. Import VSA and mimic the method's logic here
        self.second_datapoint_tastes_message_data = {
            "time_sent": self.second_datapoint_tastes_message_timestamp,
            "sender_id": self.akatosh_id,
            "chat_id": self.mock_chat_id_1,
            "text": self.second_datapoint_tastes_message_text
        }

        self.api.create(self.second_datapoint_tastes_message_data)
        akatosh_obj = self.user_api.lookup_obj(self.akatosh_id)
        self.assertAlmostEqual(
            self.expected_sentiment_after_second_datapoint,
            akatosh_obj.taste_strength(self.akatosh_taste_name)
            )
        
        # That User should now have two datapoints total on that taste
        self.assertEqual(akatosh_obj.taste_datapoints(self.akatosh_taste_name), 2)

    # Todo: Test messages ending in punctuation, e.g. "I love indian!"
