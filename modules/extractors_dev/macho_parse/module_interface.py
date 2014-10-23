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

desc = " This module parses Mach-O files."
name = "macho_parse"

import logging
from parse_macho import process_macho
import api

logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {}

def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True }

def process(oid, opts):
    logger.debug("process()")
    src_type = api.retrieve("src_type", oid, {})
    if src_type["type"] != "MACHO" and src_type["type"] != "OSX Universal Binary":
        return False
    
    src = api.source(oid)
    data = api.get_field(src, oid, "data", {})
    if not data: 
        logger.debug("Not able to process %s",oid)
        return False
        
    result = process_macho(data, oid)
    if result:
        api.store(name, oid, result, opts)
        return True
        
    return False

