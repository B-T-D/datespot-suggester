import unittest

from user import User

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):
        
        # Instantiate a User

        self.azura_name = "Azura"
        self.azura_location = (40.73517750328247, -74.00683227856715)
        self.azura_id = "1"
        
        self.azura_user_obj = User(
            user_id = self.azura_id,
            name = self.azura_name,
            current_location = self.azura_location
            )

        # Add a taste for updating
        self.existing_taste_name = "dawn"
        self.existing_taste_strength = 0.9
        self.existing_taste_datapoints = 3
        self.azura_user_obj._tastes[self.existing_taste_name] = [self.existing_taste_strength, self.existing_taste_datapoints]

    def test_init(self):
        """Was a User object instantiated?"""
        self.assertIsInstance(self.azura_user_obj, User)
    
    def test_hash(self):
        """Does the object's hash match the result obtained from separately mimicking the 
        hash method's logic?"""
        expected_hash = hash(self.azura_id)
        self.assertEqual(expected_hash, hash(self.azura_user_obj))
    
    def test_tastes_attribute_is_expected_type(self):
        """Is the empty tastes hashmap the expected type?"""
        expected_type = dict
        self.assertIsInstance(self.azura_user_obj._tastes, expected_type)
    
    def test_update_tastes_adds_new_taste(self):
        """Does update tastes method handle a taste not yet in the tastes hashmap as expected?"""
        new_taste = "dusk"
        assert new_taste not in self.azura_user_obj._tastes # confirm nothing weird happened in the test environment
        new_taste_strength = 0.9
        self.azura_user_obj.update_tastes(new_taste, new_taste_strength)
        self.assertIn(new_taste, self.azura_user_obj._tastes) # New taste should now be in hashmap

        value = self.azura_user_obj._tastes[new_taste]
        self.assertIsInstance(value, list) # The value corresponding to the string key should be a list of length two where list[0] is float and list[1] is int
        self.assertEqual(2, len(value))
        self.assertIsInstance(value[0], float)
        self.assertIsInstance(value[1], int)

        strength, datapoints = self.azura_user_obj._tastes[new_taste][0], self.azura_user_obj._tastes[new_taste][1] 
        self.assertAlmostEqual(new_taste_strength, strength) # New taste should have strength of 0.9... 
        self.assertEqual(datapoints, 1) # ...and have 1 datapoint
    
    def test_update_tastes_updates_weighted_average(self):
        """Does update_tastes method behave as expected when adding an additional datapoint for a taste already
        in the hashmap?"""
        
        # Mimic the method's math logic to separately compute the expected value
        new_datapoint_strength = 0.1
        expected_value = (self.existing_taste_strength * self.existing_taste_datapoints + new_datapoint_strength) / (1 + self.existing_taste_datapoints)

        # Add one datapoint with different value to the taste name added in setUp
        
        self.azura_user_obj.update_tastes(self.existing_taste_name, new_datapoint_strength)
        self.assertAlmostEqual(expected_value, self.azura_user_obj._tastes[self.existing_taste_name][0])  # index [0] to return the weighted strength score
        # should now have 4 total datapoints (it was hard coded to simulate having 3 preexisting)
        self.assertEqual(4, self.azura_user_obj.taste_datapoints(self.existing_taste_name))
    
    def test_taste_strength(self):
        """Does the public method for returning the current strength of a taste behave as expected?"""
        self.assertAlmostEqual(self.existing_taste_strength, self.azura_user_obj.taste_strength(self.existing_taste_name))
