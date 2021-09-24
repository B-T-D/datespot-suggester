import unittest

from project_constants import *
import models, model_interfaces, geo_utils
from database_api import DatabaseAPI


class TestHelloWorldThings(unittest.TestCase):

    def setUp(self):
        
        self.db = DatabaseAPI() # Testing on the real DB, to have restaurants
            # TODO: script that populates the test DBs with realistic restaurants en masse. And/or separate JSON map for this test
            #   (pointing to same test DB filenames for some like users, different one for datespots)
        self.user_data = model_interfaces.UserModelInterface()

        # Need user objects to instantiate a Match
        grortName = "Grort"
        self.grortCurrentLocation = (40.746667, -74.001111)
        grort_data = {
            "name": grortName,
            "current_location": self.grortCurrentLocation
        }
        self.grort_user_id = self.db.post_object({"object_model_name": "user", "object_data": grort_data})
        self.userGrort = self.user_data.lookup_obj(self.grort_user_id)

        drobbName = "Drobb"
        self.drobbCurrentLocation = (40.767376158866554, -73.98615327558278)
        drobb_data = {
            "name": drobbName,
            "current_location": self.drobbCurrentLocation
        }
        self.drobb_user_id = self.db.post_object({"object_model_name": "user", "object_data": drobb_data})
        self.userDrobb = self.user_data.lookup_obj(self.drobb_user_id)

        # distance should be approx 2610m
        # midpoint should be circa (40.75827478958617, -73.99310556132602)

        self.matchGrortDrobb = models.Match(self.userGrort, self.userDrobb)
        assert self.matchGrortDrobb.midpoint is not None
        
        # Get the candidates list that the DatabaseAPI would be giving to Match:
        self.candidate_datespots_list = self.db.get_datespots_near(
            {
                "location": self.matchGrortDrobb.midpoint
            })
    
    def test_hash(self):
        """Does the __hash__() method's return value match the value obtained by mimicking its logic in the test code?"""
        expected_hash = hash((self.grort_user_id, self.drobb_user_id))
        actual_hash = hash(self.matchGrortDrobb)
        self.assertEqual(actual_hash, expected_hash)
    
    def test_hash_output_consistent_regardless_of_user_order(self):
        """Does Match(Alice, Bob) hash to same value as Match(Bob, Alice)?"""
        expected_hash = hash(self.matchGrortDrobb)
        match_obj_flipped_members = models.Match(self.userDrobb, self.userGrort)  # Reverse the user1 and user2 roles from those in setUp
        assert match_obj_flipped_members.user1 == self.matchGrortDrobb.user2 and match_obj_flipped_members.user2 == self.matchGrortDrobb.user1
        actual_hash = hash(match_obj_flipped_members)
        self.assertEqual(actual_hash, expected_hash)
        
        # Test same for the public id property attribute
        expected_id = self.matchGrortDrobb.id
        actual_id = match_obj_flipped_members.id
        self.assertEqual(actual_id, expected_id)

        # TODO The implementation code isn't correct as of 6/10. Observed same user ID strings producing differnent Match id hashes
        #   during Postman endpoint testing. 
    
    def test_public_id_attribute_matches_hash(self):
        """Does the public Match.id attribute-property bear the expected relationship to the return value Match.__hash__()?"""
        expected_id = str(hex(hash(self.matchGrortDrobb)))[2:]  # Mimic logic in Match._id() private method
        actual_id = self.matchGrortDrobb.id
        self.assertEqual(actual_id, expected_id)

    def test_compute_midpoint(self):
        maxDelta = 0.01
        approxExpectedMidpoint = (40.75827478958617, -73.99310556132602)
        expectedLat, expectedLon = approxExpectedMidpoint
        actualLat, actualLon = self.matchGrortDrobb.midpoint
        self.assertAlmostEqual(actualLat, expectedLat, delta=expectedLat * maxDelta)
        self.assertAlmostEqual(actualLon, expectedLon, delta=expectedLat * maxDelta)
    
    def test_public_distance_attribute(self):
        """Does the public distance attribute-property return the expected distance?"""
        expected_distance = geo_utils.haversine(self.grortCurrentLocation, self.drobbCurrentLocation)
        actual_distance = self.matchGrortDrobb.distance
        self.assertAlmostEqual(actual_distance, expected_distance)
    
    def test_get_suggestions_return_type(self):
        """Does Match.get_suggestions() external method return the expected type?"""
        expected_return_type = list
        returned_obj = self.matchGrortDrobb.suggestions(self.candidate_datespots_list)
        self.assertIsInstance(returned_obj, expected_return_type)
    
    def test_get_suggestions_return_not_null(self):
        returned_obj = self.matchGrortDrobb.suggestions(self.candidate_datespots_list)
        self.assertGreater(len(returned_obj), 0)

    def test_get_suggestions_return_shape(self):
        """Does the returned object's shape (nested lists/tuples) match the expected structure?"""
        returned_obj = self.matchGrortDrobb.suggestions(self.candidate_datespots_list)
        # each "suggestion" should be a Datespot object literal:
        for element in returned_obj:
            self.assertIsInstance(element, models.Datespot)
    
    # def test_db_user_method_returns_expected_query_results(self):
    #     """Does the method that calls the main database API return the expected query results, i.e. 
    #     a list of serialized restaurant object dicts sorted by distance?"""
    #     returned_obj = self.matchGrortDrobb._get_datespots_by_geography()
    #     #print(returned_obj)
    #     self.assertIsInstance(returned_obj, list)
    #     self.assertGreater(len(returned_obj), 0)
    
    def test_internal_scorer_method_returns_expected_data(self):
        """Does the internal "private" method responsible for scoring each nearby datespot return a non-empty
        list?"""
        returned_obj = self.matchGrortDrobb._score_nearby_datespots(self.candidate_datespots_list)
        self.assertIsInstance(returned_obj, list)
        self.assertGreater(len(returned_obj), 0)

if __name__ == "__main__":
    unittest.main()