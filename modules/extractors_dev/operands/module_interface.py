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

"""
Extracts at most one operand per instruction from disassembly. The position of
the operand is specified as an option. Operands are returned in the order they
were encountered in the physical file; non-existant operands will be None. The
structure of an operand can be found in linear_disassembly.
"""

desc = " Extract operands from a disassembly"
name = "operands"

import logging
import api
logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {"position": {"type": int, "mangle": True, "default": 0} }
    
def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True}
            
def process(oid, opts):
    logger.debug("process()")
    insns = api.get_field("disassembly", [oid], "insns", {})

    pos = opts["position"]
    
    if insns:
        operands = get_operands (insns, pos)
    else:
        operands = list() # empty list
        
    api.store(name, oid, {"operands":operands}, opts)
    return True

def get_operands (insns, pos):
    sequence = list()

    offsets = insns.keys()
    offsets.sort()

    for ofs in offsets:
        operands = list()
	if 'd_op' in insns[ofs]:
            operands += [insns[ofs]['d_op']] 
        if 's_ops' in insns[ofs]:
            operands += insns[ofs]['s_ops']
            
        if pos > len(operands)-1:
            op = None
        else:
            op = operands[pos]
            
        sequence.append (op)

    return sequence

