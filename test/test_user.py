import unittest

import models

class TestHelloWorldThings(unittest.TestCase):
    """Quick non-brokenness tests."""

    def setUp(self):
        
        # Instantiate a User

        self.azura_name = "Azura"
        self.azura_location = (40.73517750328247, -74.00683227856715)
        self.azura_id = "1"
        
        self.azura_user_obj = models.User(
            user_id = self.azura_id,
            name = self.azura_name,
            current_location = self.azura_location
            )

        # Add a taste for updating
        self.existing_taste_name = "dawn"
        self.existing_taste_strength = 0.9
        self.existing_taste_datapoints = 3
        self.azura_user_obj._tastes[self.existing_taste_name] = [self.existing_taste_strength, self.existing_taste_datapoints]

        # Instantiate second user for __eq__
        self.boethiah_name = "Boethiah"
        self.boethiah_location = (40.76346250260515, -73.98013893542904)
        self.boethiah_id = "2"
        self.boethiah_user_obj = models.User(
            user_id = self.boethiah_id,
            name = self.boethiah_name,
            current_location = self.boethiah_location
        )

        # Instantiate third user
        self.hircine_name = "Hircine"
        self.hircine_location = (40.76525023033338, -73.96722141608099)
        self.hircine_id = "3"
        self.hircine_user_obj = models.User(
            user_id = self.hircine_id,
            name = self.hircine_name,
            current_location = self.hircine_location
        )

        # Create a match between Azura and each of the other two users
        self.match_obj_azura_boethiah = models.Match(
            user1 = self.azura_user_obj,
            user2 = self.boethiah_user_obj
        )
        self.azura_user_obj.add_match(self.match_obj_azura_boethiah.id, self.match_obj_azura_boethiah.timestamp, self.boethiah_user_obj.id)
        # Manually add to azura object's matches

        self.match_obj_hircine_azura = models.Match(  # Have Azura be user2 for this one
            user1 = self.hircine_user_obj,
            user2 = self.azura_user_obj
        )
        # Manually add to azura object's matches
        self.azura_user_obj.add_match(self.match_obj_hircine_azura.id, self.match_obj_hircine_azura.timestamp, self.hircine_user_obj.id)

        

    def test_init(self):
        """Was a User object instantiated?"""
        self.assertIsInstance(self.azura_user_obj, models.User)
    
    def test_eq(self):
        """Does the custom __eq__() behave as expected?"""
        self.assertTrue(self.azura_user_obj == self.azura_user_obj)
        self.assertFalse(self.azura_user_obj == self.boethiah_user_obj)
    
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
