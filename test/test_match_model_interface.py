import unittest
import json
import random

from project_constants import *

try:
    from python_backend.model_interfaces import MatchModelInterface, UserModelInterface
except:
    from model_interfaces import MatchModelInterface, UserModelInterface

import models


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

        self.api = MatchModelInterface(json_map_filename = TEST_JSON_DB_NAME)
        self.user_api = UserModelInterface(json_map_filename = TEST_JSON_DB_NAME)

        # Create users in order to create a match.
        grortName = "Grort"
        grortCurrentLocation = (40.746667, -74.001111)

        drobbName = "Drobb"
        drobbCurrentLocation = (40.767376158866554, -73.98615327558278)

        self.userKeyGrort = self.user_api.create({"name":grortName, "current_location": grortCurrentLocation, "force_key": "1"})
        self.userKeyDrobb = self.user_api.create({"name":drobbName, "current_location": drobbCurrentLocation, "force_key": "2"})
        self.userGrort = self.user_api.lookup_obj(self.userKeyGrort)
        self.userDrobb = self.user_api.lookup_obj(self.userKeyDrobb)

        # Create a match for lookup
        self.userKeyMiltrudd = self.user_api.create({"name":"Miltrudd", "current_location":(41.0, -72.0), "force_key": "3"})
        self.userMiltrudd = self.user_api.lookup_obj(self.userKeyMiltrudd)
        # match Grort with Miltrudd:
        self.knownMatchKey = self.api.create({"user1_id": self.userKeyGrort, "user2_id": self.userKeyMiltrudd})
        assert isinstance(self.knownMatchKey, str)

    def test_instantiation(self):
        self.assertIsInstance(self.api, MatchModelInterface)

    def test_create(self):
        matchKey = self.api.create({"user1_id": self.userKeyGrort, "user2_id": self.userKeyDrobb})
        self.assertIsInstance(matchKey, str)
        expectedMatchKey = hex(hash((self.userKeyGrort, self.userKeyDrobb)))[2:] # match key should be a tuple of the two users' ids (and then mimick the logic of Match model's _id method)
        self.assertEqual(matchKey, expectedMatchKey)
    
    def test_lookup_match(self):
        matchObj = self.api.lookup_obj(self.knownMatchKey)
        self.assertIsInstance(matchObj, models.Match)
        # matchObj.id should be identical to the known match key:
        self.assertEqual(matchObj.id, self.knownMatchKey)

# todo need very thorough testing of the get_suggestions stuff. Very buggy and slapped together as of 5/13.

if __name__ == '__main__':
    unittest.main()