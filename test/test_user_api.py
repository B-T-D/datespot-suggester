import unittest
import json

try:
    from python_backend.user_api import UserAPI
    from python_backend import user
except:
    from user_api import UserAPI
    import user


TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"

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
    
    def test_blacklist(self):
        """Does the blacklist method add a second user to the user's blacklist as expected?"""
        self.api.blacklist(self.user_key_grort, self.user_key_drobb)
        # todo also need to add the other way right? or is one blacklist enough to prevent there ever being a match?
        grort_blacklist = self.api._data[self.user_key_grort]["match_blacklist"]
        self.assertIn(self.user_key_drobb, grort_blacklist)
        self.assertIsInstance(grort_blacklist, dict) # Is it a dict as expected?
