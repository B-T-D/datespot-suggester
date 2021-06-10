# TODO Rename to database_interface. This and the HTTP server run on the same (virtual) machine, that's 
#   why they communicate with named pipes. It's not a separate "Web server" and "DB server" because
#   the Node process and the Python process *must* run on the same machine, as set up here.

# TODO the req and res should be arr/list, not obj/dict, so that the packet size can always be the very first
#   thing into the pipe, right?

"""
Protocol for transmissions between Node and Python:
    - Requests and Responses are JSON-legal strings.
    - Requests state the packet size in bytes, then provide the main request as nested JSON
    - Responses state the packet size in bytes, a binary status code, and the main response as nested JSON
    - Status codes are 0 for normal response, 1 for error
    - If error, the main response JSON provides an error message.

Request format:

    request (str) = {
        "packet_size": <int>,
        "body_json": {
            "method": <str>,
            "json_arg": {<args to the relevant DatabaseAPI method>}
        }
    }

Response format:

    response (str) = {
        "packet_size": <int>,
        "status_code": <int>,
        "body_json": <return value of the underlying DatabaseAPI method, or error message>
    }

"""

from multiprocessing import Process, Pipe # TODO Tbd if there will be any communication between Python processes that can use this instead of the IPC FIFO pipes

import os
import select
from typing import ByteString
import json

from database_api import DatabaseAPI

import argparse
import time
import sys

FIFO_WEB_TO_DB = 'http-server/fifo_node_to_python'
FIFO_DB_TO_WEB = 'http-server/fifo_python_to_node'

DEFAULT_PACKET_SIZE = 1024

class DatabaseServer:

    def __init__(self):

        self._pipe_in = None
        self._pipe_out = None

        self._valid_database_methods = { # TODO Programmatically list all public methods of DatabaseAPI class, for easier maintenance.
                                        #   See https://stackoverflow.com/questions/1911281/how-do-i-get-list-of-methods-in-a-python-class
                                        # Probably need to parse to get only methods and only methods that don't start with underscore.
            "get_next_candidate",
            "get_login_user_info",
            "post_object",
            "post_decision",
            "get_matches_list",
            "get_suggestions_list"
        }

        self._error_messages = {
            "invalid dict size": lambda dict_len : f"Invalid dict length: {dict_len}",
            "invalid method": lambda method : f"Invalid method: {method}",
            "no method": lambda : f"Request didn't specify method for DatabaseAPI call"  # If some of them are weirdly lambdas, at least slightly less confusing if all of them are
        }
    
    def _read_request_bytes(self, packet_size=DEFAULT_PACKET_SIZE):
        """
        Read packet_size bytes from inbound pipe.

        Args:
            packet_size (int): Number of bytes to read. Defaults to the max packet size constant.
        
        Returns:
            (bytesring): Bytestring of the bytes read from the pipe.
        """
        # TODO Do we transmit the number of bytes in the data right before the data as an int of known byte length,
        #   and then use the number of bytes thereby specified as "n"?
        #   Or, instead, just reassemble split packets as needed? Would still need to transmit start/end signals to do that.

        # TODO what's the max buffer size on the machine on which this server would be running?

        # TODO see https://stackoverflow.com/questions/2078053/packets-down-a-named-pipe-single-byte-buffer-or-pre-sized for discussion
        #   of approaches. Seems like best practice is a TCP/IP-like protocol whereby packet headers state the size of the incoming data.

        # TODO for reference...
        # This JSON string is 103 bytes per sys.getsizeof():
        #   '{"name": "Azura", "location": [70.867567, -44.098098]}'
        # Python integer object 103 is 28 bytes (not the size of the int literal in the pipe, the size of the python object and its overhead)

        # TODO it may be, in practice, that if only sending JSON, none of the transmissions will be anywhere near the max buffer size,
        #   and that setting a comfortably large buffer won't cause problems. These are strings not image files.
        # TODO OTOH, might need to know the size to tell where one transmission ends and the next begins.

        return os.read(self._pipe_in, packet_size)
    
    def _handle_request(self):
        """
        Returns:
            (ByteString): Bytes ready to be written into the outbound DB->Web pipe
        """
        request_bytes = self._read_request_bytes()
        request_json = self._decode_request_bytes(request_bytes)
        response_json = self._dispatch_request(request_json)
        return response_json.encode("utf-8")
        
    def _decode_request_bytes(self, request_bytes: ByteString):
        assert isinstance(request_bytes, ByteString)
        request_json = request_bytes.decode("utf-8")  # TODO "ENCODING" global constant?
        return request_json

    def _validate_request(self, request_dict: dict) -> dict:
        """Returns error-message dict if request is not appropriate to pass to DatabaseAPI, else returns dict with status code 0 and no other content,
        for further methods to complete response body."""
        response_dict = {}
        error_message = None
        if not "method" in request_dict:
            error_message = self._error_messages["no method"]()
        elif request_dict["method"] not in self._valid_database_methods:
            error_message = self._error_messages["invalid method"](request_dict["method"])
        elif len(request_dict) != 2:  # Should have exactly two keys: Method and arguments dict
            error_message = self._error_messages["invalid dict size"](len(request_dict))

        if error_message:
            response_dict["status_code"] = 1
            response_dict["body_json"] = error_message
        else:
            response_dict["status_code"] = 0
        
        return response_dict

    def _dispatch_request(self, request_json: str) -> str:
        request_dict = json.loads(request_json)
        request_dict = request_dict["body_json"] # Continue with only the body JSON, packet size not relevant going forward 
        response_dict = self._validate_request(request_dict)
        if response_dict["status_code"] == 0:
            method, query_data = request_dict["method"], request_dict["query_data"]
            db = DatabaseAPI() # Let it use default JSON map
            try:
                eval_string =  f"db.{method}(query_data=query_data)"
                database_response = eval(eval_string)
            except Exception as e:
                print(f"exception raised by database call")
                response_dict["status_code"] = 1
                print(repr(e))
                database_response = f"Database error: {repr(e)}"  # TODO Pass the Exception from DB API back through the pipe same as any other error message
            if isinstance(database_response, dict):
                response_dict["body_json"] = database_response
            else:
                response_dict["body_json"] = database_response
        # TODO figure out the right way to get the packet size correctly and efficiently. NB especially that Python string or int object
        #   with its various Python methods has more bytes than the underlying raw data in memory.
        response_packet_size = sys.getsizeof(json.dumps(response_dict)) # TODO duplicative call to json.dumps, surely a better way
        response_packet_size += sys.getsizeof(response_packet_size)
        response_dict["packet_size"] = response_packet_size
        response_json = json.dumps(response_dict)
        return response_json

    def run_listener(self):
        """Listens for data transmitted through the web -> DB pipe."""
        try:
            os.mkfifo(FIFO_WEB_TO_DB) # Create inbound pipe (web -> DB)
        except FileExistsError: # TODO it should never already exist in this namespace, right? Because that would mean a non-normal
                                #   exit happened, since this script is supposed to remove both named pipes as its last action.
            print(f"Named pipe web -> DB already existed; continuing")
        
        try:
            self._pipe_in = os.open(FIFO_WEB_TO_DB, os.O_RDONLY | os.O_NONBLOCK) # Open Web->DB pipe read-only and in non-blocking mode
            print("Python inbound pipe-end ready")

            while True: # Wait for the web server to create the DB->Web pipe
                try:
                    self._pipe_out = os.open(FIFO_DB_TO_WEB, os.O_WRONLY) # Outbound DB-Web pipe is write-only
                    print("Python outbound pipe-end ready")
                    break
                except FileNotFoundError: # Fail loudly on other errors
                    pass # If file not created yet, keep trying
            
            try:
                poll = select.poll()
                poll.register(self._pipe_in, select.POLLIN)

                try:
                    while True:  # TODO what's the best polling frequency?
                        if (self._pipe_in, select.POLLIN) in poll.poll(1000):  # Poll every 1 second
                            print(f"--------  received request at {time.time()} --------")
                            response = self._handle_request()
                            os.write(self._pipe_out, response)
                
                finally:
                    poll.unregister(self._pipe_in)
            finally:
                os.close(self._pipe_in)
        finally:
            os.remove(FIFO_WEB_TO_DB)
            os.remove(FIFO_DB_TO_WEB)

if __name__ == "__main__":
    server = DatabaseServer()
    server.run_listener()