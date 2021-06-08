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
            "json_arg": {"user_id": "1"}
        }

        self.invalid_request_method_body_dict = copy.copy(self.valid_request_body_dict)  # Same dict except change the valid method to an invalid one
        self.invalid_request_method_body_dict["method"] = "corge_grault"

        self.invalid_request_no_method_body_dict = copy.copy(self.valid_request_body_dict)
        del self.invalid_request_no_method_body_dict["method"]

        self.valid_request_body_json = json.dumps(self.valid_request_body_dict)

        self.valid_request_dict = {
            "packet_size": 200,
            "body_json": self.valid_request_body_json
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

        expected_response_dict = {
            "status_code": 0
        }

        expected_body_json = self.db.get_login_user_info(json.dumps(self.valid_request_body_dict["json_arg"])) # Make the same request to the DB without going through DB server
        expected_response_dict["body_json"] = json.loads(expected_body_json)
        #expected_packet_size = sys.getsizeof(json.dumps(expected_response_dict))
        #expected_packet_size += expected_packet_size
        expected_packet_size = 240  # TODO hardcoded
        expected_response_dict["packet_size"] = expected_packet_size

        expected_response_json = json.dumps(expected_response_dict)

        actual_response_json = self.server._dispatch_request(self.valid_request_json)
        self.assertEqual(actual_response_json, expected_response_json)
