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

import struct

def resolve_target_operand( insn, header, file_data, funcs = {} ):
    target_op = insn.get("d_op", None)
    if target_op == None:
        return None
    target = None
    if header.is_64bit():
        address_length = 8
    else:
        address_length = 4
    if target_op["type"] == "eff_addr":
        ea = target_op["data"]
        if (ea["base"] == None) and (ea["idx"] == None):
            # no registers involved; let's discover the target addr
            # this is the contents of memory at location ea['disp']
            offset = header.get_offset(ea['disp'])
            if not offset or offset+address_length > len(file_data):
                return None
            if address_length == 4:
                dest_addr = struct.unpack("=L", file_data[offset:offset+address_length])[0]
            else:
                dest_addr = struct.unpack("=Q", file_data[offset:offset+address_length])[0]
            if dest_addr != 0:
                target = dest_addr 
    elif target_op["type"] in ("reg"):
        target = decode_register_usage(insn, funcs)
    elif target_op["type"] not in ['seg_off']:
        target = target_op["data"]
    return target
    
def decode_register_usage(insn, funcs):
    addr = insn["addr"]
    func = None
    for f in funcs:
        if addr >= funcs[f]["start"] and addr < funcs[f]["end"]:
            func = f
            break
    if not func: return None
    register = insn.get("d_op", None)
    found = False
    val = None
    insns = list(funcs[f]["insns"])
    insns.reverse()
    index = 0
    while(addr != insns[index]["addr"]):
        index += 1
    insns = insns[index:]
    for i in insns:
        if i["mnem"] in ("mov") and i.get("d_op", None) == register:
            found = True
            operand = i.get("s_ops")[0]["data"]
            if isinstance(operand, int):
                val = operand
            elif "disp" in operand:
                val = operand["disp"]
            break               
    return val


def instruction_to_string(insn):
    ''' Return an ASCII representation of instruction.
        This is basically
             PREFIX MNEMONIC DEST, SRC, IMM '''
    buf = insn["mnem"] + " "
    ops = []
    if "d_op" in insn and insn["d_op"]:
        ops.append(op_to_string(insn["d_op"]))
    if "s_op" in insn and insn["s_op"]:
        ops.extend([op_to_string(op) for op in insn["s_op"]])
    if "s_ops" in insn and insn["s_ops"]:
        ops.extend([op_to_string(op) for op in insn["s_ops"]])
    ops = [o for o in ops if o]
    buf += ",".join(ops)
    return buf
    
def op_to_string(op):
    if op["type"] in ("reg", "imm", "off", "rel", "register", "immediate",):
        try:
            return hex(op["data"])
        except TypeError:
            return str(op["data"])
    elif op["type"] in ("seg_off", "segment_offset"):
        return ":".join([hex(op["data"][0]), hex(op["data"][1])])
    elif op["type"] in ("eff_addr", "effective_address"):
        d = op["data"]
        buf = '['
        if d["base"]:
            try:
                buf += hex(d["base"])
            except TypeError:
                buf += str(d["base"])
        if len(buf)>1 and d["disp"]:
            buf += " + "
        if d["disp"]:
            buf += hex(d["disp"])
        if d["scale"]:
            buf += " * " + hex(d["scale"])
        if len(buf)>1 and d["idx"]:
            buf += " + "
        if d["idx"]:
            try:
                buf += hex(d["idx"])
            except TypeError:
                return str(d["idx"])
        buf += "]"
        return buf
    else:
        try:
            return hex(op["data"])
        except TypeError:
            return str(op["data"])
        
def get_slice(opts):
    start = stop = 0
    if isinstance(opts["slice"], int):
        start = opts["slice"]
        return start, stop
    
    slice = opts["slice"].split(":")
    if len(slice) == 1:
        start = stop = slice[0]
    elif len(slice) == 2:
        if slice[0]:
            start = int(slice[0])
        if slice[1]:
            stop = int(slice[1])
    else:
        raise SyntaxError("Invalid slice")
    return start, stop
 