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

import logging, xmlrpclib
import sys_utils
from SimpleXMLRPCServer import SimpleXMLRPCServer

name = "client"
logger = logging.getLogger(name)

class proxy_wrapper:
    def __init__(self, proxy):
        methods = proxy.system.listMethods()
        self.system = proxy.system
        for m in methods:
            if m == "import_file":
                setattr(self, m, decode_file(getattr(proxy, m)))
            else:
                setattr(self, m, decode(getattr(proxy, m)))

def get_proxy(server_ip, server_port, wrapped=False):
    server_string = "http://" + server_ip + ":" + str(server_port)
    my_proxy = xmlrpclib.ServerProxy(server_string, allow_none=True)
    if not my_proxy.alive():
        logger.error("Not able to connect to server %s", server_string)
        return None
    
    logger.debug("Connect to server %s", server_string)
    if wrapped:
        return proxy_wrapper(my_proxy) 
    return my_proxy  

def decode_file(f):
    def wrapper(*args, **kwargs):
        try:
            # Pack the vars before transmitting
            new_args = []
            for arg in args: 
                new_args.append(sys_utils.pack_file(arg))
            new_args = tuple(new_args)
            
            # Pack the key word vars before transmitting
            new_kwargs = {}
            for k in kwargs:
                new_kwargs[k] = sys_utils.pack_file(kwargs[k])
            res = f(*new_args, **new_kwargs)
            result = sys_utils.unpack_file(res) # unpack the result
            return result
        
        except MemoryError:
            logger.error("MemoryError while trying to decode_file")
            return None
        
    return wrapper
    
def decode(f):
    def wrapper(*args, **kwargs):
        try:
            # Pack the vars before transmitting
            new_args = []
            for arg in args: 
                new_args.append(sys_utils.pack(arg))
            new_args = tuple(new_args)
            
            # Pack the key word vars before transmitting
            new_kwargs = {}
            for k in kwargs:
                new_kwargs[k] = sys_utils.pack(kwargs[k])
            res = f(*new_args, **new_kwargs)
            result = sys_utils.unpack(res) # unpack the result
            return result
        
        except MemoryError:
            print "MemoryError while trying to decode"
            return None
        
    return wrapper
