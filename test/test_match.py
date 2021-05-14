import unittest

import json

from match import Match
import datespot
from user import User

from database_api import DatabaseAPI

TEST_JSON_MAP_FILENAME = "testing_mockJsonMap.json"

class TestHelloWorldThings(unittest.TestCase):

    def setUp(self):
        
        self.db = DatabaseAPI()

        # Need user objects to instantiate a Match
        grortName = "Grort"
        grortCurrentLocation = (40.746667, -74.001111)
        grort_json = json.dumps({
            "name": grortName,
            "current_location": grortCurrentLocation
        })
        self.grort_user_id = self.db.post_object("user", grort_json)
        userGrort = self.db.get_obj("user", self.grort_user_id)

        drobbName = "Drobb"
        drobbCurrentLocation = (40.767376158866554, -73.98615327558278)
        drobb_json = json.dumps({
            "name": drobbName,
            "current_location": drobbCurrentLocation
        })
        self.drobb_user_id = self.db.post_object("user", drobb_json)
        userDrobb = self.db.get_obj("user", self.drobb_user_id)

        # distance should be approx 2610m
        # midpoint should be circa (40.75827478958617, -73.99310556132602)

        self.matchGrortDrobb = Match(userGrort, userDrobb)
    
    def test_compute_midpoint(self):
        maxDelta = 0.01
        approxExpectedMidpoint = (40.75827478958617, -73.99310556132602)
        expectedLat, expectedLon = approxExpectedMidpoint
        actualLat, actualLon = self.matchGrortDrobb.midpoint
        self.assertAlmostEqual(actualLat, expectedLat, delta=expectedLat * maxDelta)
        self.assertAlmostEqual(actualLon, expectedLon, delta=expectedLat * maxDelta)
    
    def test_get_suggestions_return_type(self):
        """Does Match.get_suggestions() external method return the expected type?"""
        expected_return_type = list
        returned_obj = self.matchGrortDrobb.get_suggestions()
        self.assertIsInstance(returned_obj, expected_return_type)
    
    def test_get_suggestions_return_not_null(self):
        returned_obj = self.matchGrortDrobb.get_suggestions()
        self.assertGreater(len(returned_obj), 0)

    def test_get_suggestions_return_shape(self):
        """Does the returned object's shape (nested lists/tuples) match the expected structure?"""
        returned_obj = self.matchGrortDrobb.get_suggestions()
        # each "suggestion" should be a Datespot object literal:
        #print(len(returned_obj))
        for element in returned_obj:
            #print(f"element = {element}: {element.name}")
            self.assertIsInstance(element, datespot.Datespot)
    
    def test_db_user_method_returns_expected_query_results(self):
        """Does the method that calls the main database API return the expected query results, i.e. 
        a list of serialized restaurant object dicts sorted by distance?"""
        returned_obj = self.matchGrortDrobb._get_datespots_by_geography()
        #print(returned_obj)
        self.assertIsInstance(returned_obj, list)
        self.assertGreater(len(returned_obj), 0)
    
    def test_internal_scorer_method_returns_expected_data(self):
        """Does the internal "private" method responsible for scoring each nearby datespot return a non-empty
        list?"""
        returned_obj = self.matchGrortDrobb._score_nearby_datespots()
        self.assertIsInstance(returned_obj, list)
        self.assertGreater(len(returned_obj), 0)

if __name__ == "__main__":
    unittest.main()