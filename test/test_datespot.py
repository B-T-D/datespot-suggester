import unittest, json

from datespot import Datespot

from database_api import DatabaseAPI

TEST_JSON_DB_NAME = "test/testing_mockJsonMap.json"
DATESPOT_SCORE_DECIMAL_PLACES = 4

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):

        self.terrezanos_location = (40.72289821341384, -73.97993915779077)
        self.terrezanos_id = hash(self.terrezanos_location) # need to manually create the key, since intializing a Datespot directly from the model, rather than via the helper API. 
            # todo set an environment variable designating the hash function to use? Function will probably change.
        self.terrezanos_name = "Terrezano's"
        self.terrezanos_traits = {
            "italian": [1.0, "discrete"],
            "wine": [0.5, 1],
            "pasta": [0.6, 2],
            "NOT FROM PIZZA HUT": [0.01, 2],
            "authentic": [-0.05, 3],
            "warehouse": [1.0, "discrete"]
            }
        self.terrezanos_price_range = 3
        self.terrezanos_hours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now

        self.terrezanos = Datespot(
            location=self.terrezanos_location,
            name=self.terrezanos_name,
            traits=self.terrezanos_traits,
            price_range=self.terrezanos_price_range,
            hours=self.terrezanos_hours
        )

        # Make mock user to test scoring:
        
        self.db = DatabaseAPI(json_map_filename=TEST_JSON_DB_NAME)

        grortName = "Grort"
        grortCurrentLocation = (40.746667, -74.001111)
        grort_json = json.dumps({ # todo can't create with tastes like this under current setup
            "name": grortName,
            "current_location": grortCurrentLocation
        })
        self.grort_tastes = {
            "italian": [0.1, 1]
        }
        self.grort_user_id = self.db.post_object("user", grort_json)
        self.user_grort = self.db.get_obj("user", self.grort_user_id)
        print(self.user_grort.serialize())
        print(f"user obj ._tastes: type = {type(self.user_grort._tastes)}\n val = \n {self.user_grort._tastes}")
        self.user_grort._tastes = self.grort_tastes # todo quick hack to force it into the data
        print(f"user obj ._tastes: type = {type(self.user_grort._tastes)}\n val = \n {self.user_grort._tastes}")
        print(self.user_grort.serialize())

    
    def test_baseline_scoring_data_read_from_json(self):
        """Did the universal baseline scoring data read in from the persistent JSON as expected?"""
        self.assertIsInstance(self.terrezanos.baseline_trait_weights, dict)
        self.assertIn("fast food", self.terrezanos.baseline_trait_weights) # Spot check an arbitrary hardcoded key expected to be in the baseline scoring weights
    
    def test_persistent_name_reputations_data_read_from_json(self):
        """Did the various reputational traits hardcoded to the restaurant's name read in from the JSON as expected?"""
        self.assertIsInstance(self.terrezanos.brand_reputations, dict)
        for tagged_restaurants in self.terrezanos.brand_reputations.values():
            self.assertIsInstance(tagged_restaurants, set)

    def test_score(self):
        """Does the internal scorer method return a score as expected?"""
        expected_score = round(0.1 * (2/3), DATESPOT_SCORE_DECIMAL_PLACES) # todo hardcoded. NB for "gameplay" balance, this (2/3) is the score you get if it matches a genre you like and you know nothing else about the restaurant.
        actual_score = self.terrezanos._score(self.user_grort)
        self.assertAlmostEqual(expected_score, actual_score)
