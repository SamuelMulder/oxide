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

desc = " Produce a histogram of types of exec (call, jmp, etc) targets"
name = "exec_target_histogram"

import logging
import api

from histogram import merge_histo
from collections import defaultdict
logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {}

def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True}

def mapper(oid, opts, jobid=False):
    logger.debug("mapper()")

    if api.exists(name, oid, opts):
        return oid
    functions = api.retrieve("function_extract", oid)
    if not functions:
        return None
    out_histo = defaultdict(int)
    for f in functions:
        l = calls(functions[f])
        out_histo = merge_histo(out_histo, l)
    api.store(name, oid, out_histo, opts)
    return oid

def reducer(intermediate_output, opts, jobid):
    logger.debug("reducer()")
    out_histo = defaultdict(int)
    for oid in intermediate_output:
        if oid:
            histo = api.retrieve(name, oid, opts)
            out_histo = merge_histo(histo, out_histo)
            if oid == jobid:
                return out_histo
    api.store(name, jobid, out_histo, opts)
    return out_histo

def calls(function):
    c = defaultdict(int)
    run = 0
    for i in function["insns"]:
        if i["group"] in ("exec"):
            c[i["mnem"]] = c[i["mnem"]] + 1 
            if 'd_op' in i:
                s = i["mnem"] + " : " + i["d_op"]["type"]
                c[s] = c[s] + 1
    return c
