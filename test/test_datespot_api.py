import unittest
import json
import random

from python_backend.datespot_api import DatespotAPI
from python_backend.datespot import Datespot

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

        # create a fake DB
        self.api = DatespotAPI(datafile_name = TEST_JSON_DB_NAME)

        # make a mock restaurant
        self.cached_location_key = (40.72289821341384, -73.97993915779077, 0.0) # location_key[2] is a vertical coordinate for resolving hypothetically possible (x, y) collisions
        assert type(self.cached_location_key) == tuple
        terrezanosTraits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
        terrezanosHours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now
        self.mockRestaurant = Datespot(
            location = self.cached_location_key,
            name = "Terrezano's",
            traits = terrezanosTraits,
            price_range = 2,
            hours = terrezanosHours
            )
        
    def test_instantiation(self):
        self.assertIsInstance(self.mockRestaurant, Datespot)
    
    def test_create_datespot(self):
        domenicosLocation = (40.723889184134926, -73.97613846772394)
        domenicosTraits = ["coffee", "coffee shop", "gourmet", "americano", "knows coffee", "bricks", "burger juice"]
        domenicosPriceRange = 1
        domenicosHours = [[8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [10, 17]]

        domenicosKey = self.api.create_datespot(domenicosLocation, "Domenico's", domenicosTraits, domenicosPriceRange, domenicosHours)
        self.assertEqual(len(domenicosKey), 3)
        domenicos = self.api.load_datespot(domenicosKey)
        #self.assertIsInstance(domenicos, Datespot) # Todo cannot get this to work, even with the metaclass thing
        self.assertEqual(str(type(domenicos)), "DatespotObj")

class TestTupleVsStringKeyIssues(unittest.TestCase):
    """Tests to confirm proper handling of messiness surrounding when tuples can/can't be keys. Tuples can be 
    keys in normal Python dicts and sets, but the JSON library doesn't support tuple-keys by default. Goal is
    for tuples to be keys in the domain layer where data are Python dict literals, not strings from JSON files.
    However it's resolved, keep it out of the domain/model layer."""

    def setUp(self):
        # create a fake DB
        self.api = DatespotAPI(datafile_name = TEST_JSON_DB_NAME)

        # make a mock restaurant
        self.cached_location_key = (40.72289821341384, -73.97993915779077, 0.0) # location_key[2] is a vertical coordinate for resolving hypothetically possible (x, y) collisions
        assert type(self.cached_location_key) == tuple
        terrezanosTraits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
        terrezanosHours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now
        terrezanosPriceRange = 2
        self.mockRestaurant = Datespot(
            location = self.cached_location_key,
            name = "Terrezano's",
            traits = terrezanosTraits,
            price_range = terrezanosPriceRange,
            hours = terrezanosHours
            )
        self.api.create_datespot(self.cached_location_key, "Terrezano's", terrezanosTraits, terrezanosPriceRange, terrezanosHours)
    
    def test_string_loc_key_to_tuple(self):
        """Does the utility convert a string representation of a tuple back to the correct tuple literal?"""
        correctTuple = (40.72289821341384, -73.97993915779077, 0)
        tupleString = str(correctTuple)
        backToTuple = self.api._string_loc_key_to_tuple(tupleString)
        self.assertEqual(backToTuple, correctTuple)

        # todo risk of weird bugs from finite float precision?
        
        # Test a bunch of seeded-pseudorandom floats with many decimal places
        random.seed(1) # seed = 1
        for randomCoordinates in range(100):
            
            coords = []
            latitude = random.randint(-90, 90)
            latitude += random.random() # todo what is the max decimal places supported by Google maps API?
            latitude = round(latitude, 14) # They paste from Google maps GUI with 14 decimal places as of May 2021
            coords.append(latitude)

            longitude = round(random.randint(-180, 180) + random.random(), 14)
            coords.append(longitude)

            # vertical:
            vertical = round(random.randint(-200, 200) + random.random(), 2) # https://en.wikipedia.org/wiki/ISO_6709, apparently standard is to express height/depth as float indicating number of meters
            coords.append(vertical)
            
            correctTuple = tuple(coords)

            # with open('test/log_randomseedcoords.txt', 'a') as fobj: # uncomment to log the random coords
            #     fobj.write(str(correctTuple) + "\n")
            #     fobj.close


            tupleString = str(correctTuple)
            self.assertEqual(self.api._string_loc_key_to_tuple(tupleString), correctTuple)


    def test_key_is_tuple_in_python_dict(self):
        """Is the key a tuple in the dictionary literal (api.data), and is the stringified tuple not in it?"""
        self.assertIn(self.cached_location_key, self.api.data)
        self.assertNotIn(str(self.cached_location_key), self.api.data)

if __name__ == '__main__':
    unittest.main() # todo the other ones need this for unittest to run them without pytest.