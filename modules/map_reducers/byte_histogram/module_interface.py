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

desc = " This module produces a histogram of the bytes in a file." 
name = "byte_histogram"        

import logging
from collections import defaultdict
from histogram import build_histo, merge_histo
import api

logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {} 
   
def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True }

def mapper(oid, opts, jobid=False):
    logger.debug("mapper()")
    src = api.source(oid)
    if api.exists(name, oid, opts):
        return oid
    data = api.get_field(src, oid, "data")
    if not data:
        return None
    out_histo = build_histo(data)
    api.store(name, oid, out_histo, opts)
    return oid
        
def reducer(intermediate_output, opts, jobid):
    logger.debug("reducer()")
    out_histo = defaultdict(int)

    for oid in intermediate_output:
        if oid:
            histo = api.retrieve(name, oid, opts)
            out_histo = merge_histo(histo, out_histo)
    api.store(name, jobid, out_histo, opts)
    
    return out_histo          
