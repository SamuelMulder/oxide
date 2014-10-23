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

desc = " Correlate call instructions with functions"
name = "map_calls"        

import re_lib
import logging
import api
import struct
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
    
    disasm = api.get_field("disassembly", oid, "insns")
    if not disasm:
        return False

    file_data = api.get_field(api.source(oid), oid, "data")
    if not file_data:
        return False

    internal_functions = api.retrieve("function_extract", oid)
    mapping = {}
    imps = {}
    ord_map = api.load_reference("ordinal_map")

    src_type = api.get_field("src_type", oid, "type")    
    if src_type == "PE":    
        imports = header.symbol_table
        
        for i in imports:
            if isinstance(imports[i]['name'], str): # we have a name
                imps[i] = imports[i]['name']
            else:   # we have an ordinal
                dll_name = imports[i]["dll"].lower()
                if dll_name in ord_map:
                    if imports[i]['name'] in ord_map[dll_name]:
                        imps[i] = ord_map[dll_name][imports[i]['name']]
                if i not in imps:
                    imps[i] = dll_name + ":Ordinal " + str(imports[i]['name'])
            
    data = { "system_calls":{},
             "internal_functions":{},
             "unresolved_calls":{}
           }
    
    # Find location of jump table.  Calls in program will call these stubs which then
    # jump to external functions.
    for i in disasm:
        insn = disasm[i]
        if insn["mnem"] in ("jmp"):
            target_op = insn.get("d_op", None)
            if not target_op:
                continue
            if isinstance(target_op["data"], int):
                target = target_op["data"]
            elif "disp" in target_op["data"]: 
                target = target_op["data"]["disp"]
            else:
                continue
            if target in imps:
                mapping[insn["addr"]] = imps[target]
                data["system_calls"][i] = imps[target]
    
    for i in disasm:
        insn = disasm[i]
        target = 0
        if insn["mnem"] in ("call", "callcc"):
            if insn['d_op']['type'] == 'eff_addr' and not insn['d_op']['data']['base']:
                target = insn['d_op']['data']['disp']
            else: 
                target = re_lib.resolve_target_operand(insn, header, file_data, internal_functions)
            if target in mapping: 
                data["system_calls"][i] = mapping[target] 
            elif target in imps: 
                data["system_calls"][i] = imps[target] 
            elif target in internal_functions: 
                data["internal_functions"][i] = internal_functions[target]["name"]
            else:
                data["unresolved_calls"][i] = target
            
                    
    api.store(name, oid, data, opts)
    return True