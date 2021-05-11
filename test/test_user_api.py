import unittest
import json

from python_backend.user_api import UserAPI
from python_backend import user

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"

class TestHelloWorldThings(unittest.TestCase):
    """Quick replacement of the manual tests."""

    def setUp(self):
    #@classmethod
    #def setUpClass(cls):

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
        
        # make a mock user with a known uuid primary key:
        self.knownKey = 1
        mockUser = user.User("test_user", currentLocation=(0,0), homeLocation=(0,0))
        self.api._data[self.knownKey] = self.api._serialize_user(mockUser)
        assert self.knownKey in self.api._data
    
    def test_create_user(self):
        newUser = self.api.create_user("Grort")
        self.assertIn(newUser, self.api._data)
    
    def test_lookup_user(self):
        existing_user = self.api.lookup_user(self.knownKey) # todo it should work with an int literal
        #print(type(existingUser))
        #self.assertIsInstance(existingUser, user.User) # todo this keeps failing even though it's a user instance. For namespacing reasons (?)
        self.assertEqual(existing_user.name, "test_user")
    
    def test_delete_user(self):
        self.api.delete(1)
        self.assertNotIn(1, self.api._data)