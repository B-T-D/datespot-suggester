import unittest

from match import Match, haversine
from user import User

class TestHelloWorldThings(unittest.TestCase):

    def setUp(self):
        
        # Need user objects to instantiate a Match
        grortName = "Grort"
        grortCurrentLocation = (40.746667, -74.001111)
        userGrort = User(grortName, grortCurrentLocation)

        drobbName = "Drobb"
        drobbCurrentLocation = (40.767376158866554, -73.98615327558278)
        userDrobb = User(name=drobbName, currentLocation = drobbCurrentLocation)

        # distance should be approx 2610m
        # midpoint should be circa (40.75827478958617, -73.99310556132602)

        self.matchGrortDrobb = Match(userGrort, userDrobb)

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
    
    def test_compute_midpoint(self):
        maxDelta = 0.01
        approxExpectedMidpoint = (40.75827478958617, -73.99310556132602)
        expectedLat, expectedLon = approxExpectedMidpoint
        actualLat, actualLon = self.matchGrortDrobb.midpoint
        self.assertAlmostEqual(actualLat, expectedLat, delta=expectedLat * maxDelta)
        self.assertAlmostEqual(actualLon, expectedLon, delta=expectedLat * maxDelta)

