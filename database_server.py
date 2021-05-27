# Plan 5/27: This is one end of named pipes, the Node web server is the other.


from multiprocessing import Process, Pipe # TODO Tbd if there will be any communication between Python processes that can use this instead of the IPC FIFO pipes

import os
import select


from database_api import DatabaseAPI

import argparse
import time
import sys

IPC_FIFO_NAME_A = "ponche_a" # the named pipes that will be used to communicate with Node
IPC_FIFO_NAME_B = "ponche_b"

def foo(q):
    q.put(f"test {time.time()}")

class DatabaseServer:

    def __init__(self, server_conn):
        """
        Args:
            receiver_conn(multiprocessing.Connection): Receiver connection.
        """
        self.conn = server_conn

    def _handle_request(self, request):
        print(f"server received request:\ntype {type(request)}\ncontent: {request}")
        if request == "get users":
            db = DatabaseAPI()
            response = db.get_all_json("user")
            return response

    def main(self):
        keep_alive = True
        while keep_alive:
            if self.conn.poll():
                request = self.conn.recv() # TODO NB the request/response can be native python objects--this isn't an HTTP server per se
                response = self._handle_request(request)
                self.conn.send(response)

class DatabaseTerminal:
    def __init__(self, client_conn):
        self.conn = client_conn
    
    def _render_response(self, response): # response can be anything able to travel via the pipe
        print(f"response ({type(response)}): \n{response}")

    def main(self):
        keep_alive = True
        while keep_alive:
            print(f"---------")
            if self.conn.poll(timeout=1): # it needs to asynchronously wait til the response comes, otherwise the next iteration of the while loop is too quick
                response = self.conn.recv()
                self._render_response(response)
            data = input(">>> ")
            print(f"data = {data}")
            print(f"self.conn = {self.conn}")
            self.conn.send(data) 
            
        

def main():
    server_conn, client_conn = Pipe(duplex=True)
    server_process = Process(target=DatabaseServer(server_conn).main)
    # TODO if you didn't want to use the DB server at the command line, you could just return the connection, right?

    # TODO: Check sys argv for a flag that says to start a DB terminal

    server_process.start()

    DatabaseTerminal(client_conn).main()


    
    

if __name__ == "__main__":
    main()