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

import logging, xmlrpclib, types, random
import oxide, oxide_server, api, server
import multiproc as mp
from sys_utils import pack, unpack
from client import get_proxy

name = "distribution_server"
logger = logging.getLogger(name)

oxide.config.distributed_enabled = False
server_list = oxide.config.distributed_compute_nodes.split()
server_port = oxide.config.distributed_port
num_servers = len(server_list)
random.seed()

print " - Servers list: " + ", ".join(server_list)
print " - Servers port:", server_port
 
functions = [oxide_server.encode(getattr(oxide, f)) for f in dir(oxide) if isinstance(getattr(oxide, f), types.FunctionType)]
functions.extend( [oxide_server.encode(getattr(api, f)) for f in dir(api) if isinstance(getattr(api, f), types.FunctionType)] )
 
def get_random_server_ip():
    r = random.randint(0,num_servers-1)
    return server_list[r]    

def retrieve(mod_name, oid_list, opts={}):
    proxy_list = []
    oid_list = unpack(oid_list)
    mod_name = unpack(mod_name)
    opts = unpack(opts)

    for server_ip in server_list:
        proxy_list.append((server_ip, server_port))
    if not isinstance(oid_list, list):
        oid_list = [oid_list]
    new_oid_list = []
    for oid in oid_list:
        if not oxide.exists(mod_name, oid, opts):
            new_oid_list.append(oid)
    if new_oid_list:
        mp.multi_map_distrib(proxy_list, mod_name, new_oid_list, opts)
    proxy = get_proxy(server_ip, server_port, wrapped=True)
    return pack(proxy.retrieve(mod_name, oid_list, opts))
    
def process(mod_name, oid_list, opts={}, force=False):
    proxy_list = []
    for server_ip in server_list:
        proxy_list.append((server_ip, server_port))
    oid_list = unpack(oid_list)
    mod_name = unpack(mod_name)
    opts = unpack(opts)
    return pack(mp.multi_map_distrib(proxy_list, mod_name, oid_list, opts, True, force))

    
functions.extend([retrieve, process])

def main(my_ip, my_port):
    if not server.init(my_ip, my_port, functions):
       print " - Not able to initiate server!"
       return 
    print " Listening on %s:%s" % (my_ip, my_port) 
    print " <CTRL-C> to quit."
    try:
        server.start_listen()
    except KeyboardInterrupt:
        server.close()
