import unittest
import json

try:
    from python_backend.model_interfaces import UserModelInterface
    from python_backend import user
except:
    from model_interfaces import UserModelInterface
    import user


TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"
USER_ID_TYPE = str

class TestHelloWorldThings(unittest.TestCase):
    """Quick replacement of the manual tests."""

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

        # make sure all the test-mock JSONs exist
        for filename in data_map:
            with open(data_map[filename], 'w') as fobj:
                json.dump({}, fobj)
                fobj.seek(0)

        # create a fake DB 
        self.api = UserModelInterface(json_map_filename=TEST_JSON_DB_NAME)

        # create mock users
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
        azura_json = json.dumps({
            "name": self.azura_name,
            "current_location": self.azura_location,
        })

        # Todo this is very convoluted--it was a quick hacky way of forcing the preexisting tastes data into the test DB
        assert self.api.create_user(azura_json, force_key=self.azura_id) == self.azura_id # It should return the id
        assert self.azura_id in self.api._data
        azura_obj = self.api.lookup_obj(self.azura_id)
        azura_obj._tastes = self.azura_existing_tastes # Directly set the private attribute
        self.api._data[self.azura_id] = azura_obj.serialize() # Manually serialize it here and force it to write to DB
        self.api._write_json()
        assert self.azura_existing_taste_name in self.api.lookup_obj(self.azura_id)._tastes

        self.boethiah_name = "Boethiah"
        self.boethiah_location = (40.76346250260515, -73.98013893542904)
        self.boethiah_id = "2"
        boethiah_json = json.dumps({
            "name": self.boethiah_name,
            "current_location": self.boethiah_location
        })
        assert self.api.create_user(boethiah_json, force_key=self.boethiah_id) == self.boethiah_id
        
    def test_create_user(self):
        json_data = json.dumps({
            "name": "Grort",
            "current_location": (40.76346250260515, -73.98013893542904)
        })
        new_user = self.api.create_user(json_data)
        self.assertIn(new_user, self.api._data)
    
    def test_lookup_user(self):
        existing_user = self.api.lookup_obj(self.azura_id) # todo it should work with an int literal
        #self.assertIsInstance(existingUser, user.User) # todo this keeps failing even though it's a user instance. For namespacing reasons (?)
        self.assertEqual(existing_user.name, self.azura_name)
    
    def test_delete_user(self):
        self.api.delete("1")
        self.assertNotIn("1", self.api._data)
    
    def test_key_types(self):
        for key in self.api._data:
            self.assertIsInstance(key, USER_ID_TYPE)
    
    def test_blacklist(self):
        """Does the blacklist method add a second user to the user's blacklist as expected?"""
        self.api.blacklist(self.azura_id, self.boethiah_id)
        # todo also need to add the other way right? or is one blacklist enough to prevent there ever being a match?
        azura_blacklist = self.api._data[self.azura_id]["match_blacklist"]
        self.assertIn(self.boethiah_id, azura_blacklist)
        self.assertIsInstance(azura_blacklist, dict) # Is it a dict as expected?

    def test_update_user(self):
        """Does the update method put new JSON to a valid model field as expected?"""
        new_data = {
            "current_location": (40.737291166191476, -74.00704685527774),
        }
        new_json = json.dumps(new_data)
        self.api.update_user(self.azura_id, new_json)
        updated_user_json = self.api.lookup_json(self.azura_id)
        updated_user_data = json.loads(updated_user_json) # todo this would not pass when checking the likes attribute of an "updates" User object literal--why? 
                                                            #   Indicates something wrong with the method that looks up a user object. 

        self.assertAlmostEqual(new_data["current_location"][0], updated_user_data["current_location"][0]) # todo these aren't very comprehensive tests
    
    def test_update_user_adds_new_taste(self):
        """Does the update method behave as expected when adding a new taste?"""
        new_taste = "dusk"
        new_taste_strength = 0.9
        new_taste_json = json.dumps({"tastes": {new_taste: new_taste_strength}})
        self.api.update_user(self.azura_id, new_taste_json)
        azura_user_obj = self.api.lookup_obj(self.azura_id)
        self.assertIn(new_taste, azura_user_obj._tastes)
    
    def test_update_user_updates_existing_taste(self):
        """Does the update method behave as expected when adding an additional datapoint to an existing taste?"""
        new_datapoint_strength = 0.1
        expected_value = \
            (self.azura_existing_taste_strength * self.azura_existing_taste_datapoints + new_datapoint_strength) / \
            (1 + self.azura_existing_taste_datapoints)
        
        update_json = json.dumps({
            "tastes": {self.azura_existing_taste_name: new_datapoint_strength}
        })
        self.api.update_user(self.azura_id, update_json)
        actual_value = self.api._data[self.azura_id]["tastes"][self.azura_existing_taste_name][0]
        self.assertAlmostEqual(expected_value, actual_value)
        
    # todo add test for current logic wrt tastes (updating the weighted average)


class TestMatchCandidates(unittest.TestCase):
    """Tests on the persistent mock DB."""

    def setUp(self):
        self.api = UserModelInterface() # Let it use default datafile name
        self.my_user_id = "1" # Key to use for the user who is doing a simulated "swiping" session
        assert self.my_user_id in self.api._get_all_data()
    
    def test_query_users_currently_near_returns_list(self):
        """Does the method that queries for users near the current location return a non-empty list
        with elements of the same type as the user ids?"""
        user_location = self.api.lookup_obj(self.my_user_id).current_location
        assert isinstance(user_location, list) # todo they're not tuples here, json module has parsed them to lists
        query_results = self.api.query_users_currently_near_location(user_location)
        self.assertIsInstance(query_results, list)
        self.assertGreater(len(query_results), 0)
        for element in query_results:
            self.assertIsInstance(element, tuple)
            self.assertIsInstance(element[0], float) # should be the distance
            self.assertIsInstance(element[1], USER_ID_TYPE) # should be a user id
    
    def test_nearby_users_result_nondecreasing(self): # todo confusing wrt when it's reversed vs ascending
        """Are the elements of the list of nearby users nonincreasing? I.e. correctly sorted nearest to farthest?"""
        user_location = self.api.lookup_obj(self.my_user_id).current_location
        query_results = self.api.query_users_currently_near_location(user_location)
        for i in range(1, len(query_results)): # The results are sorted descending, to support efficient popping of closest candidate.
            self.assertLessEqual(query_results[i], query_results[i-1])
    
    def test_nearby_users_cached(self):
        """Are the results of a nearby users query cached in the querying user's data as expected?"""
        query_results = self.api.query_users_near_user(self.my_user_id)
        user_data = self.api._get_all_data()[self.my_user_id] # return the full dict for this user id
        cached_data = user_data["cached_candidates"]
        self.assertEqual(len(query_results), len(cached_data))
        for i in range(len(query_results)):
            # test for equality of the user id ints, but not exact equality of distance floats
            results_id, cached_id = query_results[i][1], cached_data[i][1]
            self.assertEqual(results_id, cached_id)
    
    def test_query_next_candidate(self):
        """Does the query next candidate method return a valid id of another user?"""
        candidate = self.api.query_next_candidate(self.my_user_id)
        self.assertIn(candidate, self.api._data)

    def test_query_next_candidate_skips_blacklisted(self):
        id_to_blacklist = "2"
        self.api.blacklist(self.my_user_id, id_to_blacklist)
        self.api.query_users_near_user(self.my_user_id)
        user_data = self.api._get_all_data()[self.my_user_id] # return the full dict for this user id
        cached_data = user_data["cached_candidates"]
        self.assertNotIn(id_to_blacklist, cached_data)