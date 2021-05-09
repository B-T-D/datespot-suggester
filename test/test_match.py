import unittest

from match import Match
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
    
    def test_compute_midpoint(self):
        maxDelta = 0.01
        approxExpectedMidpoint = (40.75827478958617, -73.99310556132602)
        expectedLat, expectedLon = approxExpectedMidpoint
        actualLat, actualLon = self.matchGrortDrobb.midpoint
        self.assertAlmostEqual(actualLat, expectedLat, delta=expectedLat * maxDelta)
        self.assertAlmostEqual(actualLon, expectedLon, delta=expectedLat * maxDelta)