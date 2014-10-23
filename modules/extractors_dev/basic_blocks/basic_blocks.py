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

def build_basic_blocks(functions, header, file_data):
    bbs = {}
    for f in functions:
        bb_list = build_function_bbs(functions, functions[f]["insns"], header, file_data)
        bbs[f] = bb_list
    return bbs
    
def build_function_bbs(functions, insns, header, file_data):
    bbs = []
    bb_info = {}
    bb = []
    targets = find_targets(insns, header, file_data, functions)
    for i in insns:
        if i["addr"] in targets and bb:
            bb_info["first_insn"] = bb[0]['addr']
            bb_info["last_insn"] = bb[-1]['addr']
            bb_info["num_insns"] = len(bb)
            bbs.append(bb_info)
            bb_info = {}
            bb = []
        bb.append(i)
        if i["group"] in ("exec"): #and i["mnem"] not in ("call", "callcc"):
            bb_info["first_insn"] = bb[0]['addr']
            bb_info["last_insn"] = bb[-1]['addr']
            bb_info["num_insns"] = len(bb)
            bbs.append(bb_info)
            bb_info = {}
            bb = []
    if bb:
        bb_info["first_insn"] = bb[0]['addr']
        bb_info["last_insn"] = bb[-1]['addr']
        bb_info["num_insns"] = len(bb)
        bbs.append(bb_info)

    return bbs 

def find_targets(insns, header, file_data, functions):
    targets = set()
    for a in insns:
        if a["group"] in ("exec"):
            target = re_lib.resolve_target_operand(a, header, file_data, functions)
            if target: targets.add(target)
    return targets

