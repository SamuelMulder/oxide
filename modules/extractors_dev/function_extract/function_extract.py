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
import struct

def extract_functions(insns, header, file_data):
    insns_addrs = insns.keys()
    insns_addrs.sort()
    file_entry_addresses = header.get_entries()
    all_branch_targets = []
    functions = {}
    f_insns = []
		
    targets = find_call_targets(insns, header, file_data)
    for a in insns_addrs: #iterate over sorted addresses
        this_insn = insns[a]
        if this_insn["addr"] not in targets:
            #if len(f_insns) > 0 and this_insn["addr"] > f_insns[-1]["addr"] + f_insns[-1]["len"] + 1:
            if len(f_insns) > 0:
                next_addr = f_insns[-1]["addr"]+f_insns[-1]["len"]+1
                next_offset = header.get_offset(next_addr)
                if next_offset and file_data[next_offset:next_offset + 32] == "\x00"*32:
                    function = make_function(f_insns)
                    if function: functions[ function["insns"][0]["addr"] ] = function
                    f_insns = []
            f_insns.append( this_insn )
            if this_insn["mnem"] in ("hlt", "ret"): #, "jmp"): #is_controlflow_insn(this_insn):
                jtargs = find_jump_targets(f_insns, header, file_data)
                end_of_func = True
                for j in jtargs:
                    if j > this_insn["addr"] and header.find_section(this_insn["addr"]) == header.find_section(j):
                        end_of_func = False
                if not end_of_func:
                    continue
                function = make_function(f_insns)
                if function: functions[ function["insns"][0]["addr"] ] = function
                f_insns = []
        else:
            if len(f_insns) > 0:
                function = make_function(f_insns)
                if function: functions[ function["insns"][0]["addr"] ] = function
                f_insns = []
            f_insns.append(this_insn)
    if len(f_insns) > 0:
        function = make_function(f_insns)
        if function: functions[ function["insns"][0]["addr"] ] = function
        f_insns = []
        f_insns.append(this_insn)
    pruned = prune_functions(functions, targets, file_data)
    for p in pruned:
        del functions[p]
    for f in functions:
        functions[f]["name"] = "internal_function_" + str(f)
    return functions

def make_function(f_insns):
    function = {}
    int3_count = 0
    found_non_int3_jmp = False
    for i in f_insns:
        if i["mnem"] in ("int3", "jmp", "call", "nop"):
            int3_count += 1
        else: 
            found_non_int3_jmp = True
            break
    if not found_non_int3_jmp:
        return None
    f_insns = f_insns[int3_count:]
    while f_insns[-1]["mnem"] in ("int3", "nop"):
        f_insns = f_insns[:-1]
    function["insns"] = f_insns
    function["start"] = f_insns[0]["addr"]
    function["end"] = f_insns[-1]["addr"] + f_insns[-1]["len"]
    return function

def prune_functions(functions, targets, file_data):
    pruned = []
    for f in functions:
        end = functions[f]["insns"][len(functions[f]["insns"])-1]["addr"]
        int3s = True
        for i in functions[f]["insns"]:
            if i["mnem"] not in ("int3", "nop"):
                int3s = False
                break
        if int3s:
            pruned.append(f)
            continue
        for i in functions[f]["insns"]:
            if i["mnem"] == "invalid" and f not in targets:
                pruned.append(f)
                continue
    pruned = set(pruned)
    return pruned
                
def find_call_targets( insns, header, file_data ):
    targets = set()
    for a in insns:
        if insns[a]["mnem"] in ("call", "callcc"):
            target = re_lib.resolve_target_operand( insns[a], header, file_data )
            if target: targets.add(target)
    return targets

def find_jump_targets( insns, header, file_data ):
    targets = set()
    for a in insns[:-1]:
        if a["group"] in ("exec") and a["mnem"] not in ("call", "callcc", "ret", "retn"):
            target = re_lib.resolve_target_operand( a, header, file_data )
            if target: targets.add(target)
    return targets

def find_function_call_targets( insns, header, file_data ):
    targets = set()
    for a in insns:
        if a["mnem"] in ("call", "callcc"):
            target = re_lib.resolve_target_operand( a, header, file_data )
            if target: targets.add(target)
    return targets

