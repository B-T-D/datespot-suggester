# Plan 5/27: This is one end of named pipes, the Node web server is the other.

# TODO Rename to database_interface. This and the HTTP server run on the same (virtual) machine, that's 
#   why they communicate with named pipes. It's not a separate "Web server" and "DB server" because
#   the Node process and the Python process *must* run on the same machine, as set up here. 


from multiprocessing import Process, Pipe # TODO Tbd if there will be any communication between Python processes that can use this instead of the IPC FIFO pipes

import os
import select


from database_api import DatabaseAPI

import argparse
import time
import sys

FIFO_WEB_TO_DB = 'http-server/fifo_node_to_python'
FIFO_DB_TO_WEB = 'http-server/fifo_python_to_node'

def get_message(fifo):
    """
    Read n bytes from pipe.
    
    Args:
        fifo (file descriptor): File descriptor returned by os.open()
    
    Returns:

        (bytestring): A bytestring containing the bytes read

    """
    # TODO Do we transmit the number of bytes in the data right before the data as an int of known byte length,
    #   and then use the number of bytes thereby specified as "n"?

    # TODO for reference...
    # This JSON string is 103 bytes per sys.getsizeof():
    #   '{"name": "Azura", "location": [70.867567, -44.098098]}'
    # Python integer object 103 is 28 bytes (not the size of the int literal in the pipe, the size of the python object and its overhead)


    n = 24 # TODO hardcoded from example
    return os.read(fifo, n)

def process_message(message): # TODO copied from example, need to infer the typing
    """Process message read from pipe."""
    return message

# TODO can this be done the opposite way, s/t each of Node and Python creates its 
#   outbound pipe and waits on the other to create the inbound pipe? Seems more intuitive.

def fifo_read_only_kiss():
    pipe_in = os.open(FIFO_WEB_TO_DB, os.O_RDONLY | os.O_NONBLOCK)

    poll = select.poll()
    poll.register(pipe_in, select.POLLIN)

    if (pipe_in, select.POLLIN) in poll.poll(1000):
        message = get_message(pipe_in)
        message = process_message(message)
        print('----- Received from JS -----')
        print("    " + message.decode("utf-8"))



def fifo_main():
    try:
        os.mkfifo(FIFO_WEB_TO_DB) # Create the inbound pipe
    except FileExistsError:
        print(f"file already existed, continuing")
        pass

    try:
        pipe_in = os.open(FIFO_WEB_TO_DB, os.O_RDONLY | os.O_NONBLOCK) # Inbound pipe is opened as read-only and in non-blocking mode
        print("Python inbound pipe-end ready")
        print(f"Python pipe_in = {pipe_in} with type {type(pipe_in)}")

        while True: 
            try:
                print(f"Checking for Node-> Python pipe")
                pipe_out = os.open(FIFO_DB_TO_WEB, os.O_WRONLY) # Outbound pipe is write-only
                print("Python outbound pipe-end ready")
                break
            except FileNotFoundError: # If Node process didn't create its inbound pipe yet, wait until it does so
                #print(f"Python didn't find outbound (node inbound) pipe")
                print(f"waiting for Node -> Python pipe")
                time.sleep(2)
                #break
                pass
        
        try:
            poll = select.poll()
            print(f"poll = {poll}")
            poll.register(pipe_in, select.POLLIN)
            print(f"select.POLLIN = {select.POLLIN}")

            print(f"does the file descriptor have any pending I/O events?\n\t{poll.poll(1000)}")

            try:
                while True: # TODO adjust the polling frequency
                    if (pipe_in, select.POLLIN) in poll.poll(1000): # Poll every 1 second
                        message = get_message(pipe_in) # Read from the inbound pipe
                        message = process_message(message)
                        os.write(pipe_out, message) # Write to the outbound pipe

                        print('----- Received from JS -----')
                        print("    " + message.decode("utf-8")) # TODO presumably this can just go in the process message func
            finally:
                poll.unregister(pipe_in)
            
        finally:
            os.close(pipe_in)
    finally:
        os.remove(FIFO_WEB_TO_DB) # Delete the named pipes
        os.remove(FIFO_DB_TO_WEB)


if __name__ == "__main__":
    fifo_main()
    #fifo_read_only_kiss()
    