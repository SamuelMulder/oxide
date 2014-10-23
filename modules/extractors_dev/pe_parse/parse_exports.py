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
import api

from rva_offsets import rva_to_offset

logger = logging.getLogger("parse_exports")

# (name, offset, desc)
exports_directory_table_spec = [
    ("export_flags", 4, "Reserved must be 0"),
    ("time_date_stamp", 4, "Time date the export was created"),
    ("major_version", 2, "Major version number"),
    ("minor_version", 2, "Minor version number"),
    ("name_rva", 4, "RVA of the name of the DLL"),
    ("ordinal_base", 4, "Starting ordinal number usually set to 1"),
    ("address_table_entries", 4, "Number of entries in the address table"),
    ("number_of_name_pointers", 4, "Number of entries in the name pointer table"),
    ("export_address_table_rva", 4, "Address of the export address table"),
    ("name_pointer_rva", 4, "Address of the export name pointer table"),
    ("ordinal_table_rva", 4, "Address of the ordinal table"),
  ]
exports_directory_table_str = "=LLHHLLLLLLL"

exports_address_table_spec = [
    ("address", 4, "Address of the exported function or name of forwarded DLL"),
  ]
exports_address_table_str = "=L"

exports_name_pointer_table_spec = [
    ("name_pointer", 4, "Address of the name"),
  ]
exports_name_pointer_table_str = "=L"

exports_ordinal_table_spec = [
    ("ordinal", 2, "Ordinal value for the address of the export"),
  ]
exports_ordinal_table_str = "=H"

def rva_string_lookup(rva, sections, image_base, data, offsets):
    if not rva:
        return None, offsets
    f_offset = rva_to_offset(rva, sections, image_base)
    if not f_offset:   
        return None, offsets
    string_end = data[f_offset:].find("\x00")
    offsets[f_offset] = [{"len":string_end, "string":"Export Name"}]
    return data[f_offset:f_offset+string_end], offsets
    
def parse_exports_directory_table(dd, sections, optional_header, data, offsets):
    if not dd or "export_table" not in dd:
        return None, offsets
    base_rva, table_len = dd["export_table"]["virtual_address"], dd["export_table"]["length"]
    if base_rva == 0 and table_len == 0:
        return None, offsets
    
    str_len = struct.calcsize(exports_directory_table_str)
    base = rva_to_offset(base_rva, sections)
    if not base or base + str_len >= len(data):
        return None, offsets
    
    vals = {}
    val_data = struct.unpack(exports_directory_table_str, data[base:base+str_len])
    for n, elem in enumerate(exports_directory_table_spec):
        vals[elem[0]] = val_data[n]
        
    build_exports_offset_strings(vals, base, offsets)
    
    base_rva = vals["export_address_table_rva"]
    base = rva_to_offset(base_rva, sections)   
    entry_len = struct.calcsize(exports_address_table_str)
    addresses = []
    for i in xrange(vals["address_table_entries"]):
        if not base or base + entry_len >= len(data):
            break
        address = struct.unpack(exports_address_table_str, data[base:base+entry_len])
        addresses.append(address[0])
        base += entry_len
    
    base_rva = vals["name_pointer_rva"]
    base = rva_to_offset(base_rva, sections)
    if not base:
        return None, offsets
    entry_len = struct.calcsize(exports_name_pointer_table_str)
    export_names = []
    for i in xrange(vals["number_of_name_pointers"]):
        if base + entry_len >= len(data):
            break
        name_ptr = struct.unpack(exports_name_pointer_table_str, data[base:base+entry_len])
        name, offsets = rva_string_lookup(name_ptr[0], sections, optional_header["image_base"], data, offsets)
        base += entry_len
        if name:
            export_names.append(name)
    
    base_rva = vals["ordinal_table_rva"]
    base = rva_to_offset(base_rva, sections)    
    entry_len = struct.calcsize(exports_ordinal_table_str)
    ords = []
    for i in xrange(vals["number_of_name_pointers"]):
        if not base or base + entry_len >= len(data):
            break
        ord = struct.unpack(exports_ordinal_table_str, data[base:base+entry_len])
        ords.append(ord[0])
        base += entry_len
    
    exports = {}
    
    for n, o in zip(export_names, ords):
        if o < len(addresses):
            exports[n] = {"ord":o, "address":addresses[o]}
       
    vals["export_names"] = exports
    return vals, offsets

def build_exports_offset_strings(exports, base, offsets):
    offset = base
    for elem in exports_directory_table_spec:
        len = elem[1]
        s = "%s: %s (%s)"%(elem[0], exports[elem[0]], elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    return offsets
