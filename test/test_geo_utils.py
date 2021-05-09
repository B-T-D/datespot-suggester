import unittest
import random

from geo_utils import *

class TestLatLonValidator(unittest.TestCase):

    def setUp(self):
        random.seed(1)
        self.valid_latitudes, self.valid_longitudes, self.valid_locations, self.invalid_locations = [], [], [], []

        for i in range(1000):
            self.valid_latitudes.append(random.uniform(-90, 90))
            self.valid_longitudes.append(random.uniform(-180, 180))
            self.valid_locations.append((self.valid_latitudes[i], self.valid_longitudes[i]))
            self.invalid_locations.append((self.valid_latitudes[i], random.uniform(-181, -500))) # one valid one invalid
            self.invalid_locations.append((self.valid_latitudes[i], random.uniform(181, 500)))
            self.invalid_locations.append((random.uniform(-91, -500), self.valid_longitudes[i]))
            self.invalid_locations.append((random.uniform(-91, -500), self.valid_longitudes[i]))
        
        self.edge_cases = [(-90.00000000, -180.00000000), (90.00000000, -180.00000000), (-90.00000000, 180.00000000), (90.00000000, 180.00000000)]
        self.boundary_cases = [(-90.00000001, -180.00000000), (90.00000001, -180.00000000), (-90.00000001, 180.00000000), (90.00000001, 180.00000000),
        (-90.00000000, -180.00000001), (90.00000000, -180.00000001), (-90.00000000, 180.00000001), (90.00000000, 180.00000001)]

    def test_accepts_valid_locations(self):
        for location in self.valid_locations:
            self.assertTrue(is_valid_lat_lon(location))
        for location in self.edge_cases:
            self.assertTrue(is_valid_lat_lon(location))
    
    def test_rejects_invalid_locations(self):
        for location in self.invalid_locations:
            self.assertFalse(is_valid_lat_lon(location))
        for location in self.boundary_cases:
            self.assertFalse(is_valid_lat_lon(location))

class TestHaversine(unittest.TestCase):

    def test_haversine(self):
        maxDelta = 0.01 # largest difference to tolerate

        expectedGCDistanceNYCtoLondon = 5567 * 1000
        londonLatLon = (51.5074, -0.1278)
        NYCLatLon = (40.7128, -74.0060)
        actual = haversine(londonLatLon[0], londonLatLon[1], NYCLatLon[0], NYCLatLon[1])
        expected = expectedGCDistanceNYCtoLondon
        self.assertAlmostEqual(actual, expected, delta=expected*maxDelta)

        expectedGCDistanceNYCtoToronto = 574 * 1000
        torontoLatLon = (43.678720190872674, -79.63110274333383)
        actual = haversine(torontoLatLon[0], torontoLatLon[1], NYCLatLon[0], NYCLatLon[1])
        expected = expectedGCDistanceNYCtoToronto
        self.assertAlmostEqual(actual, expected, delta=expected*maxDelta)

class TestMidpoint(unittest.TestCase):

    def test_midpoint(self):
        max_delta = 0.01 # Tolerate being off by up to 1%
        location1 = (40.746667, -74.001111)
        location2 = (40.767376158866554, -73.98615327558278)
        approx_expected_midpoint = (40.75827478958617, -73.99310556132602)
        expected_lat, expected_lon = approx_expected_midpoint[0], approx_expected_midpoint[1]
        actual_lat, actual_lon = midpoint(location1, location2)
        self.assertAlmostEqual(actual_lat, expected_lat, delta=abs(expected_lat * max_delta))
        self.assertAlmostEqual(actual_lon, expected_lon, delta=abs(expected_lon * max_delta))
    