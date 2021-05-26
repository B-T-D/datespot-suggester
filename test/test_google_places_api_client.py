import unittest
import sys, os

import dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
dotenv.load_dotenv(dotenv_path)

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

from api_clients.google_places_api_client import Client

class TestClientHelloWorld(unittest.TestCase):
    """Quick non-brokenness tests for the Client class."""

    def setUp(self):
        self.client = Client()
        self.test_location_param = "40.74977666604178,-73.99597469657479" # string for direct use in the query
        self.test_location_tuple = (40.74977666604178, -73.99597469657479)
        self.bad_location_tuple = "-90.0000001,180.000001"

        self.correct_NS_request_without_page_token =\
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={GOOGLE_MAPS_API_KEY}&location=40.74977666604178,-73.99597469657479&radius=1600&type=restaurant"

    def test_live_requests_debug_toggle(self):
        """Is _allow_live_requests set to False when DEBUG is set to true?"""
        self.assertFalse(self.client._allow_live_requests)
    
    def test_live_requests_debug_toggle_vice_versa(self):
        new_client = Client(allow_live_requests=True)
        self.assertTrue(new_client._allow_live_requests)

    def test_rejects_bad_location(self):
        """Does NS request handler raise an error for invalid latitude and longitudes?"""
        with self.assertRaises(Exception):
            self.client(self.bad_location_param)

    def test_google_maps_api_key_environment_variable(self):
        """Does "GOOGLE_MAPS_API_KEY" exist as a non-null environment variable?"""
        self.assertIsNotNone(os.getenv("GOOGLE_MAPS_API_KEY"))

    def test_bad_nearby_search_rankby_raises_exception(self):
        """Does passing an invalid 'rankby' request parameter raise an exception?"""
        with self.assertRaises(Exception):
            self.client.request_gmp_nearby_search(self.test_location_param, rankby="garply")
    
    def test_nearby_search_NANDs_radius_and_rankby(self):
        """Does NS request handler require one of radius and rankby, but disallow both?"""
        with self.assertRaises(Exception):
            self.client.request_gmp_nearby_search(self.test_location_param, radius=5000, rankby="distance") # both

    def test_concatenate_querystring(self):
        """Does the querystring concatenator match an expected hardcoded string from a confirmed correct request?"""
        expected_querystring = self.correct_NS_request_without_page_token
        actual_querystring = self.client._concatenate_gmp_nearby_search_querystring(
            location=self.test_location_tuple,
            radius=1600,
            type="restaurant"
        )
        self.assertEqual(actual_querystring, expected_querystring)

