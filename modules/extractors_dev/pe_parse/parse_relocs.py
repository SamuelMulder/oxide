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

import struct, logging
from rva_offsets import rva_to_offset

logger = logging.getLogger("parse_relocs")

base_relocation_block_spec = [
    ("page_rva", 4, "Image base + page RVA + offset = address of base relocation"),
    ("block_size", 4, "Total number of bytes in the base relocation block"),
  ]  
base_relocation_block_str = "=LL"

base_relocation_spec = [
    ("type_offset", 2, "First 4 bits is the type followed by 12 bits of offset"),
  ]
base_relocation_str = "=H"  

base_relocation_type_enum = {
    0:"absolute",
    1:"high16",
    2:"low16",
    3:"high_low", # Adjust full 32 bits
    4:"high_adj", # Takes 2 slots
    5:"mips_jmpaddr_arm_mov32a", 
    7:"arm_mov32t",
    9:"mips_jumpaddr16",
    10:"dir64",
}

def parse_base_relocations(dd, sections, data, offsets):
    if not dd or "base_relocation_table" not in dd:
        return None, offsets
    base, table_len = dd["base_relocation_table"]["virtual_address"], dd["base_relocation_table"]["length"]
    if base == 0 and table_len == 0:
        return None, offsets
    entry_len = struct.calcsize(base_relocation_block_str)
    base = rva_to_offset(base, sections)
    if not base:
        return None, offsets
    offset = base
    relocations = []
    while offset - base < table_len and offset+entry_len < len(data):
        val_data = struct.unpack(base_relocation_block_str, data[offset:offset+entry_len])
        block = {}
        for n, elem in enumerate(base_relocation_block_spec):
            block[elem[0]] = val_data[n]
        
        o = offset
        for elem in base_relocation_block_spec:
            length = elem[1]
            s = "%s: %s (%s)"%(elem[0], block[elem[0]], elem[2])
            offsets[o].append({"len":length, "string":s})
            o += length
        
        rels = []
        s = block["block_size"]
        offset += entry_len
        s -= entry_len
        num_entries = s / struct.calcsize(base_relocation_str)
        rlen = struct.calcsize(base_relocation_str)
        for i in xrange(num_entries):
            if offset + rlen >= len(data):
                break
            type_offset = struct.unpack(base_relocation_str, data[offset:offset+rlen])
            type_val = (type_offset[0] & 0b1111000000000000) >> 12
            offset_val = type_offset[0] & 0b0000111111111111
            rels.append((type_val, offset_val))
            offsets[offset].append({"len":rlen, "string":"Type: %s, Offset: %s"%(type_val, offset_val)})
            offset += rlen
        block["relocations"] = rels
            
        relocations.append(block)
    
    return relocations, offsets

