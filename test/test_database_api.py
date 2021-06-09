import unittest
import json, time

from database_api import DatabaseAPI
import models
import model_interfaces

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"

class TestHelloWorldThings(unittest.TestCase):
    """Basic non-brokenness tests."""

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
        
        # Instantiate DatabaseAPI object
        self.db = DatabaseAPI(json_map_filename = TEST_JSON_DB_NAME)

        # Data for mock users
        self.azura_name = "Azura"
        self.azura_location = (40.73517750328247, -74.00683227856715)
        self.azura_id = "1"
        self.azura_existing_taste_name = "dawn"
        self.azura_existing_taste_strength = 0.9
        self.azura_existing_taste_datapoints = 3
        self.azura_existing_tastes = { # This is the data in the object's internal format, for testing convenience not for a call to the external create_user()
            self.azura_existing_taste_name:
                [self.azura_existing_taste_strength,
                self.azura_existing_taste_datapoints]
        }

        self.azura_json = json.dumps({
            "name": self.azura_name,
            "current_location": self.azura_location,
            "force_key": self.azura_id
        })

        self.boethiah_name = "Boethiah"
        self.boethiah_location = (40.76346250260515, -73.98013893542904)
        self.boethiah_id = "2"
        self.boethiah_json = json.dumps({
            "name": self.boethiah_name,
            "current_location": self.boethiah_location,
            "force_key": self.boethiah_id
        })

        # Data for mock Datespot
        self.terrezanos_location = (40.737291166191476, -74.00704685527774)
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

        self.terrezanos_json = json.dumps({
                "location" : self.terrezanos_location,
                "name" : self.terrezanos_name,
                "traits" : self.terrezanos_traits,
                "price_range" : self.terrezanos_price_range,
                "hours" : self.terrezanos_hours,
            })
        
        self.terrezanos_id = self.db.post_object(json.dumps({"object_model_name": "datespot", "json_data": self.terrezanos_json}))

        # Data for mock Review of Terrezano's

        self.mock_text_positive_relevant = "This was a wonderful place to go on a date. I had the pasta. It was authentic and not from Pizza Hut."
        self.expected_sentiment = 0.1906 # todo hardcoded
        self.expected_relevance = round(1 / len(self.mock_text_positive_relevant), 4) # i.e. "date" appears once.
        self.terrezanos_review_json = json.dumps({
            "datespot_id": self.terrezanos_id,
            "text": self.mock_text_positive_relevant
        })


        # Add two users for use in testing compound objects
        self.db.post_object(json.dumps({"object_model_name": "user", "json_data": self.azura_json}))
        self.db.post_object(json.dumps({"object_model_name": "user", "json_data": self.boethiah_json}))

        # Data for mock Message and Chat
        self.mock_bilateral_timestamp = time.time()
        self.quick_mock_chat_json = json.dumps({
            "start_time": time.time(),
            "participant_ids": [self.azura_id, self.boethiah_id]
        })
        self.mock_chat_id_1 = self.db.post_object(json.dumps({"object_model_name": "chat", "json_data": self.quick_mock_chat_json}))  # Need a Chat to create a Message
        self.single_sentence_text = "Worship the Nine, do your duty, and heed the commands of the saints and priests."
        self.expected_sentiment_single_sentence = 0.296 # todo hardcoded

        self.mock_bilateral_message_json = json.dumps({
            "time_sent": self.mock_bilateral_timestamp,
            "sender_id": self.azura_id,
            "chat_id": self.mock_chat_id_1,
            "text": self.single_sentence_text
        })

    def test_init(self):
        """Was an object of the expected type instantiated?"""
        self.assertIsInstance(self.db, DatabaseAPI)
    
    def test_model_interface_constructor_calls(self):
        """Does the DB interface call the expected model interface for each model name?"""
        expected_interfaces = {
            "user": model_interfaces.UserModelInterface,
            "datespot": model_interfaces.DatespotModelInterface,
            "match": model_interfaces.MatchModelInterface,
            "review": model_interfaces.ReviewModelInterface,
            "message": model_interfaces.MessageModelInterface,
            "chat": model_interfaces.ChatModelInterface
        }
        for model_name in expected_interfaces:
            actual_interface = self.db._model_interface(model_name)
            self.assertIsInstance(actual_interface, expected_interfaces[model_name])
    
    def test_validate_model_name(self):
        """Does the validator raise the expected error for a bad model name?"""
        with self.assertRaises(ValueError):
            self.db._validate_model_name("foo")
    
    ### Tests for post_object() and get_object() ###

    def test_post_and_get_obj_user(self):
        talos_name = "Talos"
        talos_location = (40.76346250260515, -73.98013893542904)
        expected_talos_id = "3"
        talos_json = json.dumps({
            "name": talos_name,
            "current_location": talos_location,
            "force_key": expected_talos_id
        })
        actual_talos_id = self.db.post_object(json.dumps({"object_model_name": "user", "json_data": talos_json}))
        self.assertIsInstance(actual_talos_id, str)
        talos_obj = self.db.get_object("user", actual_talos_id)
        self.assertIsInstance(talos_obj, models.User)
        self.assertEqual(expected_talos_id, actual_talos_id)
    
    def test_post_and_get_obj_datespot(self):
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

        domenicos_json = json.dumps({
            "location" : domenicos_location,
            "name" : domenicos_name,
            "traits" : domenicos_traits,
            "price_range" : domenicos_price_range,
            "hours" : domenicos_hours
        })
        
        domenicos_id = self.db.post_object(json.dumps({"object_model_name": "datespot", "json_data": domenicos_json}))
        domenicos_obj = self.db.get_object("datespot", domenicos_id)

        self.assertIsInstance(domenicos_obj, models.Datespot)
    
    def test_post_and_get_obj_match(self):
        match_json = json.dumps({
            "user1_id": self.azura_id,
            "user2_id": self.boethiah_id
        })
        match_id = self.db.post_object(json.dumps({"object_model_name": "match", "json_data": match_json}))
        match_obj = self.db.get_object("match", match_id)
        self.assertIsInstance(match_obj, models.Match)
    
    def test_post_and_get_obj_review(self):
        review_id = self.db.post_object(json.dumps({"object_model_name": "review", "json_data": self.terrezanos_review_json}))
        review_obj = self.db.get_object("review", review_id)
        self.assertIsInstance(review_obj, models.Review)
    
    def test_post_and_get_obj_message(self):
        message_id = self.db.post_object(json.dumps({"object_model_name": "message", "json_data": self.mock_bilateral_message_json}))
        message_obj = self.db.get_object("message", message_id)
        self.assertIsInstance(message_obj, models.Message)
    
    def test_post_and_get_obj_chat(self):
        chat_id = self.db.post_object(json.dumps({"object_model_name": "chat", "json_data": self.quick_mock_chat_json}))
        chat_obj = self.db.get_object("chat", chat_id)
        self.assertIsInstance(chat_obj, models.Chat)
    
    ### Tests for get_json() ###

    def test_get_json_user(self):
        # Get the expected JSON from the model interface one layer down from the DB API being tested here:
        user_db = model_interfaces.UserModelInterface(TEST_JSON_DB_NAME)
        expected_json = user_db.lookup_json(self.azura_id)
        actual_json = self.db.get_json(json.dumps({"object_model_name": "user", "object_id": self.azura_id}))
        self.assertEqual(expected_json, actual_json)
    
    def test_get_json_datespot(self): # TODO Complete these for thoroughness. More presisng stuff 5/26; these aren't needed for simple coverage.
        pass

    def test_get_json_match(self):
        pass

    def test_get_json_review(self):
        pass

    def test_get_json_message(self):
        pass

    def test_get_json_chat(self):
        pass

    ### Tests for get_all_json() ###

    def test_get_all_json_user(self): # TODO this doesn't test the correctness of the JSON, it's a very bare non-brokenness / coverage-chasing test only
        expected_len = 2 # setUp created two mock users
        users_json = self.db.get_all_json("user")
        users_dict = json.loads(users_json)  # Load it back to a Python dict before testing len(), otherwise it's len of the string
        self.assertEqual(expected_len, len(users_dict))

    # TODO complete for other models

    ### Tests for put_json() ###

    def test_put_json_update_user(self):

        # Test updating a User's location:
        new_data = {
            "current_location": (40.737291166191476, -74.00704685527774),
        }
        self.db.put_json("user", self.azura_id, json.dumps(new_data))
        azura_obj = self.db.get_object("user", self.azura_id)
        self.assertAlmostEqual(new_data["current_location"], azura_obj.current_location)
    
    def test_updating_unsupported_model_raises_error(self):
        """Does attempting to update a model for which updates aren't supported raise the 
        expected error?"""
        unsupported_models = ["review", "message"]
        arbitrary_object_id = "a"
        arbitrary_json = json.dumps({"foo": "bar"})
        for model in unsupported_models:
            with self.assertRaises(ValueError):
                self.db.put_json(model, arbitrary_object_id, arbitrary_json)
    
    # TODO complete for other models and their main anticipated update cases

    ### Tests for post_decision() ###
    def test_post_yes_decision_no_match(self):
        """Does posting a "yes" decision that doesn't create a match return the expected JSON?"""
        decision_yes_json = json.dumps({
            "user_id": self.azura_id,
            "candidate_id": self.boethiah_id,
            "outcome": True
        })
        expected_response_json = json.dumps({
            "match_created": False
        })
        actual_response_json = self.db.post_decision(decision_yes_json)
        self.assertEqual(expected_response_json, actual_response_json)
    
    def test_post_yes_decision_yes_match(self):
        """Does posting a "yes" decision that creates a match return the expected JSON?"""
        # Post a decision of Azura liking Boethiah:
        azura_decision_yes_json = json.dumps({
            "user_id": self.azura_id,
            "candidate_id": self.boethiah_id,
            "outcome": True
        })
        self.db.post_decision(azura_decision_yes_json)

        # Post a second decision of Boethiah liking Azura
        boethiah_decision_yes_json = json.dumps({
            "user_id": self.boethiah_id,
            "candidate_id": self.azura_id,
            "outcome": True
        })

        expected_response_json = json.dumps({
            "match_created": True
        })

        actual_response_json = self.db.post_decision(boethiah_decision_yes_json)
        self.assertEqual(expected_response_json, actual_response_json)
    
    def test_post_no_decision(self):
        """Does posting a "no" decision return the expected JSON?"""
        decision_no_json = json.dumps({
            "user_id": self.azura_id,
            "candidate_id": self.boethiah_id,
            "outcome": False
        })
        expected_response_json = json.dumps({
            "match_created": False
        })
        actual_response_json = self.db.post_decision(decision_no_json)
        self.assertEqual(expected_response_json, actual_response_json)
    
    def test_non_boolean_outcome_raises_error(self):
        """Does posting JSON without a boolean outcome raise the expected error?"""
        bad_json = json.dumps({
            "user_id": self.azura_id,
            "candidate_id": self.boethiah_id,
            "outcome": 2
        })
        with self.assertRaises(TypeError):
            self.db.post_decision(bad_json)

    ### Tests for get_datespots_near() ###

    # Code that makes live API calls isn't covered by the main tests suite

    def test_get_datespots_near_cache_only_default_radius(self):
        """Does the method return a string matching the expected shape of a JSON-ified list of Datespots
        in response to a query that provides valid location but no radius?"""
        location_query_json = json.dumps({
            "location": (40.737291166191476, -74.00704685527774)
        })
        results = self.db.get_datespots_near(location_query_json)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        first_result = results[0]
        distance, datespot = first_result # it's a two-element tuple
        self.assertIsInstance(distance, float)
        self.assertIsInstance(datespot, models.Datespot)
    
    def test_get_datespots_near_cache_only_nondefault_radius(self):
        """Does the method return the expected JSON in response to a query that provides valid location
        and specifies a non-default_radius?"""
        location_query_json = json.dumps({
            "location": (40.737291166191476, -74.00704685527774),
            "radius": 4000
        })
        results = self.db.get_datespots_near(location_query_json)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        first_result = results[0]
        distance, datespot = first_result # it's a two-element tuple
        self.assertIsInstance(distance, float)
        self.assertIsInstance(datespot, models.Datespot)
    
    ### Tests for get_datespot_suggestions() ###

    def test_get_datespot_suggestions(self):
        """Does the method return the expected JSON in response to JSON matching with a valid Match?"""

        # Put a Match in the mock DB
        match_json = json.dumps({
            "user1_id": self.azura_id,
            "user2_id": self.boethiah_id
        })
        match_id = self.db.post_object(json.dumps({"object_model_name": "match", "json_data": match_json}))
        match_obj = self.db.get_object("match", match_id)

        query_json = json.dumps({
            "match_id": match_id
        })

        results = self.db.get_datespot_suggestions(query_json)
        self.assertIsInstance(results, list)
    
    ### Tests for other public methods ###
    def test_get_next_candidate(self):  # We have two Users in the DB, so one will be the other's candidate
        query_json = json.dumps({
            "user_id": self.azura_id
        })
        result = self.db.get_next_candidate(query_json)
        print(f"result = {result}")
        candidate_name = json.loads(result)["name"]
        self.assertEqual(self.boethiah_name, candidate_name)

    # TODO Post / get obj / get json for all of:
    #     user
    #     datespot
    #     match
    #     review
    #     message
    #     chat

    def test_get_matches(self):
        self.fail()
    
    def test_get_suggestions(self):
        self.fail()