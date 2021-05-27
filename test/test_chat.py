import unittest
import json 
import time

import models

from database_api import DatabaseAPI

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"
SENTIMENT_DECIMAL_PLACES = 4

class TestHelloWorldThings(unittest.TestCase):

    def setUp(self):
        # Todo: Very hard to test the model in isolation here. Because chats require messages, and current architecture is that
        #   messages are created directly into a chat. The model itself doesn't persist any data, so it's impossible for the 
        #   create_message method to find the correct chat to update. 

        # Same un-DRY boilerplate to configure the testing DB:
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

        # make sure all the test-mock JSONs exist and start as "{}":
        for filename in data_map:
            with open(data_map[filename], 'w') as fobj:
                json.dump({}, fobj)
                fobj.seek(0)

        # Mock DB
        self.db = DatabaseAPI(json_map_filename=TEST_JSON_DB_NAME)

        # Mock users

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


        # Instantiate chat object with two participants

        # Messages can't be instantiated without a Chat ID
        #   Todo and that chat ID must come from the DB. So must initiate a chat in the DB.

        self.chat_start_time = time.time()
        self.chat_json = json.dumps({
            "start_time": self.chat_start_time,
            "participant_ids": [self.akatosh_id, self.stendarr_id]
        })

        self.chat_id = self.db.post_object("chat", self.chat_json)
        

        # Mock messages

        self.first_timestamp = time.time()
        self.first_message_text = "Lord Akatosh lends you his might. When your own strength fails you, trust in the Nine."

        self.first_message_json = json.dumps({
            "time_sent": self.first_timestamp,
            "sender_id": self.akatosh_id,
            "chat_id": self.chat_id,
            "text": self.first_message_text

        })
        self.first_message_id = self.db.post_object("message", self.first_message_json)
        self.first_message_obj = self.db.get_object("message", self.first_message_id)
        self.first_message_sentiment = self.first_message_obj.sentiment

        # Second message in same chat:
        self.second_timestamp = time.time()
        self.second_message_text = "K, thanks for letting me know!"
        self.second_message_json = json.dumps({
            "time_sent": self.second_timestamp,
            "sender_id": self.stendarr_id,
            "chat_id": self.chat_id,
            "text": self.second_message_text
        })
        self.second_message_id = self.db.post_object("message", self.second_message_json)
        self.second_message_obj = self.db.get_object("message", self.second_message_id)
        self.second_message_sentiment = self.second_message_obj.sentiment

        # create_message should append the message to the chat 

        # Fetch the chat object at the end, to create one with the messages appended
        self.chat_obj = self.db.get_object("chat", self.chat_id)

    def test_init(self):
        self.assertIsInstance(self.chat_obj, models.Chat)
    
    def test_eq(self):
        """Does the custom __eq__() behave as expected?"""
        self.assertTrue(self.chat_obj == self.chat_obj)
    
    def test_message_id_order(self):
        """Are both test messages in the Chat, and is the first message before the second?"""
        # self.chat_obj.messages.append("test")
        self.assertEqual([message.id for message in self.chat_obj.messages], [self.first_message_id, self.second_message_id]) # todo hacky/obfuscating to have the list comp here
    
    def test_average_sentiment(self):
        """Does the average sentiment match the value expected from separate calculation on same values?"""
        self.assertIsNotNone(self.chat_obj.sentiment)
        expected_mean_sentiment = round((self.first_message_sentiment + self.second_message_sentiment) / 2, SENTIMENT_DECIMAL_PLACES)
        self.assertEqual(expected_mean_sentiment, self.chat_obj.sentiment)