from multiprocessing import Process, Pipe


from database_api import DatabaseAPI

import argparse
import time
import sys

def foo(q):
    q.put(f"test {time.time()}")

class DatabaseServer:

    def __init__(self, server_conn):
        """
        Args:
            receiver_conn(multiprocessing.Connection): Receiver connection.
        """
        self.conn = server_conn

    def _parse_request(self, request):
        print(f"server received request:\ntype {type(request)}\ncontent: {request}")
    
    def _form_response(self, request):
        return f"Mock response: Thank you for your request of \ntype {type(request)}\ncontent: {request}"
        

    def main(self):
        keep_alive = True
        while keep_alive:
            if self.conn.poll():
                request = self.conn.recv()
                self._parse_request(request) # request need not be a string
                response = self._form_response(request)
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