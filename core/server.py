"""
Copyright (c) 2014 Sandia Corporation. 
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation, 
the U.S. Government retains certain rights in this software.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from SimpleXMLRPCServer import SimpleXMLRPCServer
import logging, SocketServer, socket

class ForkingServer(SocketServer.ForkingMixIn, SimpleXMLRPCServer):
#class ForkingServer(SimpleXMLRPCServer):
    pass

name = "server"
logger = logging.getLogger(name)

my_server = None
def init(ip, port, functions):
    global my_server
    if not isinstance(functions, list):
        logger.error("functions must be of list type")
        return False
    my_server = ForkingServer((ip, int(port)), allow_none=True, )
    my_server.register_introspection_functions()
    my_server.register_function(alive)
    for function in functions:
        my_server.register_function(function)
        
    logger.debug("Server init %s:%s", ip, port)
    return True

def start_listen():
    logger.debug("Server listening")
    my_server.serve_forever()

def close():
    #my_server.close() # Use this for non forking server
    my_server.server_close() # Use this for forking server
    logger.debug("Server close")

def alive():
    return True
