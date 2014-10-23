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

desc = " This module does a linear disassembly of an the first basic block from the entry point."
name = "disasm_first_run"

import logging
import disassemble_entry
import api, config

logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {}

def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True }

def process(oid, opts):
    logger.debug("process()")
    src_type = api.retrieve("src_type", oid)
    source = src_type["source"]
    header_oid = oid
    if source != "files":
        return False
    file_data = api.get_field(source, oid, "data")
    header = api.get_field("object_header", [header_oid], "header")
    
    # do not disassemble under certain conditions
    if not header:
        logging.info("Not processing oid %s: unrecognized file type", oid)
        return False
    else:
        logger.info ("calling (python-based) disassemble_first_run on %s", oid)
        entries = header.get_entries()
        if not entries:
            logger.info("No entry points found for %s", oid)
            return False
        
        entry_address = entries.pop()
        functions = api.retrieve("function_extract", oid)
        if functions and entry_address in functions:
            insns = functions[entry_address]["insns"]        
        else:
            insns = disassemble_entry.disassemble_entry(file_data, header, entry_address, logger)
        data = {"type":src_type["type"], "insns":insns,
                "num_insns":len(insns), "insn_mode":header.insn_mode}
    api.store(name, oid, data, opts)
    return True
