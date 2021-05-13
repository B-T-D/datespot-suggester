import unittest
import json
import random

try:
    from python_backend.match_api import MatchAPI
    from python_backend.user_api import UserAPI
except:
    from match_api import MatchAPI
    from user_api import UserAPI

from match import Match

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"


class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

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

        self.api = MatchAPI(datafile_name = TEST_JSON_DB_NAME)
        self.user_api = UserAPI(datafile_name = TEST_JSON_DB_NAME)

        # Create users in order to create a match.
        grortName = "Grort"
        grortCurrentLocation = (40.746667, -74.001111)

        drobbName = "Drobb"
        drobbCurrentLocation = (40.767376158866554, -73.98615327558278)

        self.userKeyGrort = self.user_api.create_user(json.dumps({"name":grortName, "current_location": grortCurrentLocation}), force_key=1)
        self.userKeyDrobb = self.user_api.create_user(json.dumps({"name":drobbName, "current_location": drobbCurrentLocation}), force_key=2)
        self.userGrort = self.user_api.lookup_user_obj(self.userKeyGrort)
        self.userDrobb = self.user_api.lookup_user_obj(self.userKeyDrobb)

        # Create a match for lookup
        self.userKeyMiltrudd = self.user_api.create_user(json.dumps({"name":"Miltrudd", "current_location":(41.0, -72.0)}), force_key=3)
        self.userMiltrudd = self.user_api.lookup_user_obj(self.userKeyMiltrudd)
        # match Grort with Miltrudd:
        self.knownMatchKey = self.api.create_match(self.userKeyMiltrudd, self.userKeyGrort)

    def test_instantiation(self):
        self.assertIsInstance(self.api, MatchAPI)

    def test_create_match(self):
        matchKey = self.api.create_match(userid_1 = self.userKeyGrort, userid_2 = self.userKeyDrobb)
        self.assertIsInstance(matchKey, int)
        expectedMatchKey = hash((self.userKeyGrort, self.userKeyDrobb)) # match key should be a tuple of the two users' ids
        self.assertEqual(matchKey, expectedMatchKey)
    
    def test_lookup_match(self):
        matchObj = self.api.lookup_match(self.knownMatchKey)
        self.assertIsInstance(matchObj, Match)

if __name__ == '__main__':
    unittest.main()