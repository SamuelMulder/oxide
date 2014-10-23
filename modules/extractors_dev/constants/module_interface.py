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

desc = " Locate runs of constants instructions in disassembly"
name = "constants"        

import logging
import api
logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {} 
    
def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True}
            
def process(oid, opts):
    logger.debug("process()")
    
    insns = api.get_field("disassembly", oid, "insns")

    if insns == None:
        return False

    offsets = insns.keys()
    offsets.sort()
    count = 0
    start_offset = 0
    const_run = {}
    for offset in offsets:
        pre_count = count
        if "d_op" in insns[offset] and insns[offset]["d_op"]["type"]:    
            if insns[offset]["d_op"]["type"] == "imm":
                if count == 0:
                    start_offset = offset            
                count += 1
        if "s_ops" in insns[offset]:
            for source in insns[offset]["s_ops"]:
                if "type" in source and source["type"] == "imm":
                    if count == 0:
                        start_offset = offset
                    count +=1
        if pre_count == count:
            if count > 0:
                const_run[start_offset] = count
                count = 0
                start_offset = 0

    if count > 0:
        const_run[start_offset] = count
            
    api.store(name, oid, const_run, opts)
    return True

