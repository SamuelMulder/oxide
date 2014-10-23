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

desc = " This module does a linear disassembly of an executable file."
name = "linear_arm_disassembler"

import logging
from linear_arm_disassembler import disassemble_arm_linear
import api

logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {"force" : { "type":bool, "mangle":False, "default":"" }}

def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True }

def process(oid, opts):
    logger.debug("process()")
    src = api.source(oid)
    file_data = api.get_field(src, oid, "data")    
    hopts = {"fake":opts['force']}
    header = api.get_field("object_header", [oid], "header", hopts)
    
    if not file_data or not header:
        return False

    # do not disassemble under certain conditions
    if (not opts['force'] and not header.known_format): 
        logger.debug("Not processing oid %s: unrecognized file type", oid)
        return False
    
    logger.debug("calling (python-based) disassemble_arm_linear on %s", oid)
    insns = disassemble_arm_linear(file_data, header, logger)
    data = {"insns":insns, "num_insns":len(insns), 
        "insn_mode":header.insn_mode}
    api.store(name, oid, data, opts)
    return True

