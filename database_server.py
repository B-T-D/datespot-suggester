# Plan 5/27: This is one end of named pipes, the Node web server is the other.

# TODO Rename to database_interface. This and the HTTP server run on the same (virtual) machine, that's 
#   why they communicate with named pipes. It's not a separate "Web server" and "DB server" because
#   the Node process and the Python process *must* run on the same machine, as set up here. 


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
            "post_object"
        }
    
    def _read_request_bytes(self, bytes=DEFAULT_PACKET_SIZE):
        """
        Read bytes bytes from inbound pipe.

        Args:
            bytes (int): Number of bytes to read. Defaults to the max packet size constant.
        
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

        return os.read(self._pipe_in, bytes)
    
    def _handle_request(self):
        """

        Returns:
            (ByteString): Bytes ready to be written into the outbound DB->Web pipe
        """
        request_bytes = self._read_request_bytes()
        request_json = self._decode_request_bytes(request_bytes)
        print(f"request_json = {request_json} \n\t type {type(request_json)}\n\tlen = {len(request_json)}")
        response_json = None
        if self._is_valid_request(request_json):
            print(f"request was valid")
            response_json = self._dispatch_request(request_json)
        else:
            response_json = json.dumps({"error": f"Bad request to database server at {time.time()}"})
        print(f"response_json = {response_json}")
        return response_json.encode("utf-8")
        
    def _decode_request_bytes(self, request_bytes: ByteString):
        assert isinstance(request_bytes, ByteString)
        request_json = request_bytes.decode("utf-8")  # TODO "ENCODING" global constant?
        return request_json
    
    def _is_valid_request(self, request_json: str) -> bool:
        """Returns True if the request is appropriate JSON to pass to the DatabaseAPI, else False."""
        # TODO Can't rely on the dict being properly formatted; could be arbitrary additional keys
        #   beyond just method and json-arg
        # TODO Have a precursor helper method that strips everything from the dict except the expected keys.
        if not request_json or not isinstance(request_json, str):
            return False
        request_dict = json.loads(request_json) # TODO hypothetically are there malicious strings that would be problematic to read into a dict blindly?
        print(f"in validator: request_dict = {request_dict}\nwith type {type(request_dict)}")
        if len(request_dict) != 2: # Should have exactly two keys: Method and arguments dict/object
            print(f"Request dict should have exactly two keys, len was {len(request_dict)}")
            return False
        if not "method" in request_dict:
            print(f"method wasn't in request dict")
            return False
        elif request_dict["method"] not in self._valid_database_methods:
            print(f"invalid method: {request_dict['method']}")
            return False
        # TODO validate the args? Or is DB API best positioned to validate the args to its methods?
        return True

    def _dispatch_request(self, request_json: str):
        request_dict = json.loads(request_json)
        method, json_arg = request_dict["method"], json.dumps(request_dict["json_arg"])
        assert isinstance(json_arg, str)
        print(f"json_arg = \n{json_arg}")
        db = DatabaseAPI() # Let it use default JSON map
        response_json = eval(f"db.{method}(json_arg=json_arg)")
        print(f"in dispatch request: response_json = {response_json}")
        return response_json

    def run_listener(self):
        """Listens for data transmitted throught the web -> DB pipe."""
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
                            # TODO just one method call here, response = self.handle_request(), then write response to the out pipe
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
    