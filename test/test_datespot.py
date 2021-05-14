import unittest

from datespot import Datespot

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):

        self.terrezanos_location = (40.72289821341384, -73.97993915779077)
        self.terrezanos_id = hash(self.terrezanos_location) # need to manually create the key, since intializing a Datespot directly from the model, rather than via the helper API. 
            # todo set an environment variable designating the hash function to use? Function will probably change.
        self.terrezanos_name = "Terrezano's"
        self.terrezanos_traits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
        self.terrezanos_price_range = 3
        self.terrezanos_hours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now

        self.terrezanos = Datespot(
            location=self.terrezanos_location,
            name=self.terrezanos_name,
            traits=self.terrezanos_traits,
            price_range=self.terrezanos_price_range,
            hours=self.terrezanos_hours
        )
    
    def test_baseline_scoring_data_read_from_json(self):
        """Did the universal baseline scoring data read in from the persistent JSON as expected?"""
        self.assertIsInstance(self.terrezanos.baseline_trait_weights, dict)
        self.assertIn("fast food", self.terrezanos.baseline_trait_weights) # Spot check an arbitrary hardcoded key expected to be in the baseline scoring weights
    
    def test_persistent_name_reputations_data_read_from_json(self):
        """Did the various reputational traits hardcoded to the restaurant's name read in from the JSON as expected?"""
        self.assertIsInstance(self.terrezanos.brand_reputations, dict)
        for tagged_restaurants in self.terrezanos.brand_reputations.values():
            self.assertIsInstance(tagged_restaurants, set)