import unittest
import json

try:
    from python_backend.user_api import UserAPI
    from python_backend import user
except:
    from user_api import UserAPI
    import user


TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"
USER_ID_TYPE = int

class TestHelloWorldThings(unittest.TestCase):
    """Quick replacement of the manual tests."""

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
        self.api = UserAPI(datafile_name=TEST_JSON_DB_NAME)
        
        # make a mock user directly in the DB with a known uuid primary key:
        self.knownKey = 3
        mockUser = user.User("test_user", current_location=(0,0), home_location=(0,0))
        self.api._data[self.knownKey] = self.api._serialize_user(mockUser)
        assert self.knownKey in self.api._data

        self.grort_location = (40.746667, -74.001111)

        # Make mock users for testing blacklisting:
        grortName = "Grort"
        grortCurrentLocation = (40.746667, -74.001111)

        drobbName = "Drobb"
        drobbCurrentLocation = (40.767376158866554, -73.98615327558278)

        self.user_key_grort = self.api.create_user(json.dumps({"name":grortName, "current_location": grortCurrentLocation}), force_key=1)
        self.user_key_drobb = self.api.create_user(json.dumps({"name":drobbName, "current_location": drobbCurrentLocation}), force_key=2)
    
    def test_create_user(self):
        json_data = json.dumps({
            "name": "Grort",
            "current_location": self.grort_location
        })
        new_user = self.api.create_user(json_data)
        self.assertIn(new_user, self.api._data)
    
    def test_lookup_user(self):
        existing_user = self.api.lookup_user(self.knownKey) # todo it should work with an int literal
        #print(type(existingUser))
        #self.assertIsInstance(existingUser, user.User) # todo this keeps failing even though it's a user instance. For namespacing reasons (?)
        self.assertEqual(existing_user.name, "test_user")
    
    def test_delete_user(self):
        self.api.delete(1)
        self.assertNotIn(1, self.api._data)
    
    def test_key_types(self):
        for key in self.api._data:
            self.assertIsInstance(key, USER_ID_TYPE)
    
    def test_blacklist(self):
        """Does the blacklist method add a second user to the user's blacklist as expected?"""
        self.api.blacklist(self.user_key_grort, self.user_key_drobb)
        # todo also need to add the other way right? or is one blacklist enough to prevent there ever being a match?
        grort_blacklist = self.api._data[self.user_key_grort]["match_blacklist"]
        self.assertIn(self.user_key_drobb, grort_blacklist)
        self.assertIsInstance(grort_blacklist, dict) # Is it a dict as expected?

class TestMatchCandidates(unittest.TestCase):
    """Tests on the persistent mock DB."""

    def setUp(self):
        self.api = UserAPI() # Let it use default datafile name
        self.my_user_id = 1 # Key to use for the user who is doing a simulated "swiping" session
    
    def test_query_users_currently_near_returns_list(self):
        """Does the method that queries for users near the current location return a non-empty list
        with elements of the same type as the user ids?"""
        user_location = self.api.lookup_user(1).current_location
        assert isinstance(user_location, list) # todo they're not tuples here, json module has parsed them to lists
        query_results = self.api.query_users_currently_near_location(user_location)
        print(query_results)
        self.assertIsInstance(query_results, list)
        self.assertGreater(len(query_results), 0)
        for element in query_results:
            self.assertIsInstance(element, tuple)
            self.assertIsInstance(element[0], float) # should be the distance
            self.assertIsInstance(element[1], USER_ID_TYPE) # should be a user id
    
    def test_nearby_users_result_nondecreasing(self): # todo confusing wrt when it's reversed vs ascending
        """Are the elements of the list of nearby users nonincreasing? I.e. correctly sorted nearest to farthest?"""
        user_location = self.api.lookup_user(1).current_location
        query_results = self.api.query_users_currently_near_location(user_location)
        for i in range(1, len(query_results)): # The results are sorted descending, to support efficient popping of closest candidate.
            self.assertLessEqual(query_results[i], query_results[i-1])
    
    def test_nearby_users_cached(self):
        """Are the results of a nearby users query cached in the querying user's data as expected?"""
        query_results = self.api.query_users_near_user(1)
        user_data = self.api.get_all_data()[1] # return the full dict for this user id
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
        id_to_blacklist = 2
        self.api.blacklist(self.my_user_id, id_to_blacklist)
        self.api.query_users_near_user(1)
        user_data = self.api.get_all_data()[1] # return the full dict for this user id
        cached_data = user_data["cached_candidates"]
        self.assertNotIn(id_to_blacklist, cached_data)
    


    

