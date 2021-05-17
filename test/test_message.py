import unittest
import json
import time

from message import Message
from database_api import DatabaseAPI


TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"

class TestHelloWorldThings(unittest.TestCase):

    def setUp(self):

        # Mock DB
        self.db = DatabaseAPI(json_map_filename=TEST_JSON_DB_NAME)

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

        # Instantiate mock simple bilateral message (one recipient)

        self.mock_bilateral_timestamp = time.time()
        self.single_sentence_text = "Worship the Nine, do your duty, and heed the commands of the saints and priests."
        self.expected_sentiment_single_sentence = 0.296 # todo hardcoded
        
        self.mock_chat_id_1 = "1a"
        self.message_obj = Message(
            time_sent = self.mock_bilateral_timestamp,
            sender_id = self.akatosh_id,
            chat_id = self.mock_chat_id_1,
            text = self.single_sentence_text
        )

        # Instantiate mock multi-sentence message.
        self.multisentence_text = "I'm Akatosh blah blah blah. Lord Akatosh lends you his might. When your own strength fails you, trust in the Nine."
        self.expected_sentiment_multisentence = 0.092 # todo hardcoded

        self.mock_chat_id_2 = "2a"
        self.multisentence_message_obj = Message(
            time_sent = time.time(),
            sender_id = self.akatosh_id,
            chat_id = self.mock_chat_id_2,
            text = self.multisentence_text
        )

    def test_init(self):
        self.assertIsInstance(self.message_obj, Message)
    
    def test_hash(self):
        """Does the integer returned by __hash__ match the results of mimicing the same hashing steps
        manually?"""
        expected_hash = hash(str(self.mock_bilateral_timestamp) + self.akatosh_id)
        self.assertEqual(expected_hash, hash(self.message_obj))
    
    def test_tokenize(self):
        """Does _tokenize split a multisentence text into the expected sentences?"""
        expected_sentences = [
            "I'm Akatosh blah blah blah.",
            "Lord Akatosh lends you his might.",
            "When your own strength fails you, trust in the Nine."
        ]
        self.multisentence_message_obj._tokenize()
        for i in range(len(expected_sentences)):
            self.assertEqual(expected_sentences[i], self.multisentence_message_obj._sentences[i])

        # Todo test other sentence-ending punctuation.
    
    def test_analyze_sentiment(self):
        """Does the sentiment match the hardcoded expected sentiment?"""
        self.message_obj._analyze_sentiment()
        self.assertAlmostEqual(self.expected_sentiment_single_sentence, self.message_obj._sentiment_avg)
        self.multisentence_message_obj._analyze_sentiment()
        self.assertAlmostEqual(self.expected_sentiment_multisentence, self.multisentence_message_obj._sentiment_avg)
    
    def test_str(self):
        """Does the __str__ method return the expected string?"""
        expected_string = f"{self.mock_bilateral_timestamp}:\t{self.akatosh_id}:\t{self.single_sentence_text}"
