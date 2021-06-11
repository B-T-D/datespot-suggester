import unittest

import json, copy, sys

from database_server import DatabaseServer
from database_api import DatabaseAPI

class TestDatabaseServer(unittest.TestCase):
    """Unit tests for DatabaseServer methods that are testable without a live connection to the
    web server."""

    def setUp(self):

        self.server = DatabaseServer()
        self.db = DatabaseAPI()

        self.valid_request_body_dict = {
            "method": "get_login_user_info",
            "query_data": {"user_id": "1"}
        }

        self.invalid_request_method_body_dict = copy.copy(self.valid_request_body_dict)  # Same dict except change the valid method to an invalid one
        self.invalid_request_method_body_dict["method"] = "corge_grault"

        self.invalid_request_no_method_body_dict = copy.copy(self.valid_request_body_dict)
        del self.invalid_request_no_method_body_dict["method"]

        #self.valid_request_body_json = json.dumps(self.valid_request_body_dict)

        self.valid_request_dict = {
            "packet_size": 200,
            "body_json": self.valid_request_body_dict
        }

        self.valid_request_json = json.dumps(self.valid_request_dict)

    def test_init(self):
        self.assertIsInstance(self.server, DatabaseServer)
    
    ### Tests for direct calls to the validator ###

    def test_validate_request_returns_ok_status_code(self):
        """Does the validator method return the expected dict with an "ok" status code for a valid request?"""
        expected_response_dict = { # This wouldn't have the packet size in it yet
            "status_code": 0
        }
        actual_response_dict = self.server._validate_request(self.valid_request_body_dict)  # The validator method only gets the body dict, not the full request dict
        self.assertEqual(actual_response_dict, expected_response_dict)
    
    def test_validate_request_returns_error_status_code(self):
        """Does the validator method return the expected error dict for a request with an unsupported method?"""
        expected_response_dict = {
            "status_code": 1,
            "body_json": self.server._error_messages["invalid method"]("corge_grault")
        }
        actual_response_dict = self.server._validate_request(self.invalid_request_method_body_dict)
        self.assertEqual(actual_response_dict, expected_response_dict)
    
    def test_validate_request_returns_error_dict_no_method(self):
        """Does the validator return the expected error dict for a request that failed to specify any database method?"""
        expected_response_dict = {
            "status_code": 1,
            "body_json": self.server._error_messages["no method"]()
        }
        actual_response_dict = self.server._validate_request(self.invalid_request_no_method_body_dict)
        self.assertEqual(actual_response_dict, expected_response_dict)
    
    ### Tests for direct calls to request dispatcher ###

    def test_dispatcher_returns_ok_status_code(self):
        """Does the dispatcher return the expected json string for a valid request?"""

        expected_status_code = 0
        response = self.server._dispatch_request(self.valid_request_json)
        actual_status_code = json.loads(response)["status_code"]

        self.assertEqual(actual_status_code, expected_status_code)