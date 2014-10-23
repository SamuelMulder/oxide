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

import logging, multiprocessing, optparse, time, cPickle, types, socket
import oxide, api, server, sys_utils

name = "oxide_server"
logger = logging.getLogger(name)

oxide.config.distributed_enabled = False

def encode(f):
    def wrapper(*args, **kwargs):
        # Unpack the key word vars after being transmitted
        new_args = []
        for arg in args: 
            new_args.append(sys_utils.unpack(arg))
        new_args = tuple(new_args)
        
        # Unpack the key word vars after being transmitted
        new_kwargs = {}
        for k in kwargs:
            new_kwargs[k] = sys_utils.unpack(kwargs[k])
        
        res = f(*new_args, **new_kwargs)
        result = sys_utils.pack(res) # Pack the result before transmitting
        return result
    
    # Fixup the name and doc string for this function
    wrapper.__name__ = f.__name__
    wrapper.__doc__  = f.__doc__
    wrapper.__repr__  = f.__repr__
    return wrapper

# Wrap all of the oxide methods with the encode method
functions = [encode(getattr(oxide, f)) for f in dir(oxide) if isinstance(getattr(oxide, f), types.FunctionType)]
functions.extend( [encode(getattr(api, f)) for f in dir(api) if isinstance(getattr(api, f), types.FunctionType)] )

def main(my_ip, my_port):
    try:
       if not server.init(my_ip, my_port, functions):
           print " - Not able to initiate server. Exiting."
           return
    except socket.error as err:
       print err
       print " - Not able to initiate server. Exiting."
       return 
    print " Oxide server listening on %s:%s" % (my_ip, my_port) 
    print " <CTRL-C> to quit."
    try:
        server.start_listen()
    except KeyboardInterrupt:
        print " - Caught <CTRL-C> closing server"
        server.close()
