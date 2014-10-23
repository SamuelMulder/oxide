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

import re_lib
import networkx
import struct

def build_cfg(functions, header, file_data, all_bbs):
    cfgs = {}
    for f in functions:
        cfg = build_function_cfg(functions, functions[f]["insns"], all_bbs[f], header, file_data)
        cfgs[f] = cfg
    return cfgs
    
def build_function_cfg(functions, insns, bbs, header, file_data):
    g = networkx.DiGraph()
    bb_entries = [ bb["first_insn"] for bb in bbs ]
    for e in bb_entries:
        g.add_node(e)
    for bb in bbs:
        bb_end = bb["last_insn"]
        last_insn = None
        targets = []
        for c, i in enumerate(insns):
            if i["addr"] == bb_end:
                last_insn = c
                break
        if last_insn:
            if insns[last_insn]["group"] in ("exec"): #and insns[last_insn]["mnem"] not in ("call", "callcc"):
                target = re_lib.resolve_target_operand(insns[last_insn], header, file_data, functions)
                if target:
                    targets.append(target)
                if insns[last_insn]["mnem"] not in ("jmp", "ret", "retn") and last_insn < len(insns) - 1:
                    targets.append(insns[last_insn+1]["addr"])
            elif insns[last_insn]["mnem"] not in ("ret", "retn") and last_insn < len(insns) - 1:
                    targets.append(insns[last_insn+1]["addr"])
                
        for t in targets:
            if t in bb_entries:
                g.add_edge(bb["first_insn"], t)
    if g.size() == 0:
        g = None
    return g
    
