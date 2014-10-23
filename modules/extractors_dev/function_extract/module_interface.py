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

desc = " Extract functions from disassembly"
name = "function_extract"        

import logging
import api
from function_extract import extract_functions
logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {} 
    
def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True}
            
def process(oid, opts):
    logger.debug("process()")
    header = api.get_field("object_header", oid, "header")
    if not header:
		return False
    else:
        disasm = api.get_field("disassembly", oid, "insns")
        data = api.get_field(api.source(oid), oid, "data")
        if not disasm or not data:
            return False
        f = extract_functions(disasm, header, data)
    api.store(name, oid, f, opts)
    return True
