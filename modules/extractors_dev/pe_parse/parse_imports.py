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

logger = logging.getLogger("parse_imports")

# (name, offset, desc)
delay_import_table_spec = [
    ("attributes", 4, "Must be 0"),
    ("name_rva", 4, "RVA of the name of the DLL to be loaded"),
    ("module_handle", 4, "RVA of the module handle to be loaded"),
    ("delay_import_address_table", 4, "RVA of the delay load import address table"),
    ("delay_import_name_table", 4, "RVA of the delay import name table"),
    ("bound_delay_import_table", 4, "RVA of the bound delay load address table, if it exists"),
    ("unload_delay_import_table", 4, "RVA of the bound delay unload address table, should be an exact copy of the delay IAT"),
    ("timestamp", 4, "Timestamp of the DLL to which the image has been bound"),
  ]
delay_import_table_str = "=LLLLLLLL"

import_table_spec = [
    ("import_lookup_table", 4, "RVA of import lookup table, containing name or ordinal for each import"),
    ("time_date_stamp", 4, "Time and date, 0 until bound then set to values for the DLL"),
    ("forwarder_chain", 4, "Index of first forwarder reference"),
    ("name_rva", 4, "RVA of the ASCII string containing the name of the DLL"),
    ("import_address_table", 4, "RVA of import address table, identical to import_lookup_table until image is bound"),
  ]
import_table_str = "=LLLLL"

import_lookup_table_32_spec = [
    ("name_or_ordinal", 4, "If first bit is set, ordinal number, otherwise RVA to name"),
  ]
import_lookup_table_32_str = "=L"

import_lookup_table_64_spec = [
    ("name_or_ordinal", 8, "If first bit is set, ordinal number, otherwise RVA to name"),
  ]
import_lookup_table_64_str = "=Q"

def rva_string_lookup(rva, sections, image_base, data, offsets):
    if not rva:
        return None, offsets
    f_offset = rva_to_offset(rva, sections, image_base)
    if not f_offset:   
        return None, offsets
    string_end = data[f_offset:].find("\x00")
    offsets[f_offset] = [{"len":string_end, "string":"Import Name"}]
    return data[f_offset:f_offset+string_end], offsets
    
def parse_import_lookup_table(base, base_rva, optional_header, sections, data, offsets):
    if not base:
        return None, offsets
    pe_type = optional_header["magic_type"]
    if pe_type == 0x20b:
        spec = import_lookup_table_64_spec
        s = import_lookup_table_64_str
    else:
        spec = import_lookup_table_32_spec
        s = import_lookup_table_32_str
    
    entry_len = struct.calcsize(s)
    vals = []
    offset = base
    while offset + entry_len < len(data):
        val_data = struct.unpack(s, data[offset:offset+entry_len])
        if val_data[0] == 0:
            break
        if ( (pe_type == 0x20b and val_data[0] & 0x8000000000000000) or
             (pe_type != 0x20b and val_data[0] & 0x80000000) ):
            ordinal = val_data[0] & 0xff
            vals.append(ordinal)
            offsets[offset].append({'len':entry_len, 'string':"Import ordinal"})    
        else:
            name_rva = val_data[0]
            name, offsets = rva_string_lookup(name_rva+2, sections, optional_header["image_base"], data, offsets)
            if not name:  
                break
            vals.append(name)
            offsets[offset].append({'len':entry_len, 'string':"RVA to import name"})
        
        offset += entry_len
                
    return vals, offsets

def parse_import_address_table(base, base_rva, optional_header, sections, data, offsets):
    if not base:
        return None, offsets
    pe_type = optional_header["magic_type"]
    if pe_type == 0x20b:
        spec = import_lookup_table_64_spec
        s = import_lookup_table_64_str
    else:
        spec = import_lookup_table_32_spec
        s = import_lookup_table_32_str
    
    entry_len = struct.calcsize(s)
    vals = {}
    offset = base
    rva = base_rva
    while offset + entry_len < len(data):
        val_data = struct.unpack(s, data[offset:offset+entry_len])
        if not val_data[0]:
            break
        if ( (pe_type == 0x20b and val_data[0] & 0x8000000000000000) or
             (pe_type != 0x20b and val_data[0] & 0x80000000) ):
            ordinal = val_data[0] & 0xff
            vals[rva + optional_header["image_base"]] = ordinal    
        else:
            name_rva = val_data[0]
            name, offsets = rva_string_lookup(name_rva+2, sections, optional_header["image_base"], data, offsets)
            if not name:  
                break
            vals[rva + optional_header["image_base"]] = name
        offset += entry_len
        rva += entry_len
                
    return vals, offsets

def parse_import_table(dd, sections, optional_header, data, offsets):
    if not dd or "import_table" not in dd:
        return None, offsets
    base_rva, table_len = dd["import_table"]["virtual_address"], dd["import_table"]["length"]
    if not base_rva or not table_len:
        return None, offsets
        
    base = rva_to_offset(base_rva, sections)
    if not base or base + table_len > len(data):
        return None, offsets
    
    vals = {}
    entry_len = struct.calcsize(import_table_str)
    current_offset = base
    while current_offset - base < table_len and current_offset + entry_len < len(data):
        val_data = struct.unpack(import_table_str, data[current_offset:current_offset+entry_len])
        check = 0
        for v in val_data:
            if v != 0:
                check = 1; break
        if not check:
            break
        import_entry = {}
        for offset, elem in enumerate(import_table_spec):
            import_entry[elem[0]] = val_data[offset]
        name_rva = import_entry["name_rva"]
        if not name_rva:
            continue
        name, offsets = rva_string_lookup(name_rva, sections, optional_header["image_base"], data, offsets)
        lookup_table_rva = import_entry["import_lookup_table"]
        lookup_table_offset = rva_to_offset(lookup_table_rva, sections)
        function_names, offsets = parse_import_lookup_table(lookup_table_offset, lookup_table_rva, optional_header, sections, data, offsets)
        address_table_rva = import_entry["import_address_table"]
        address_table_offset = rva_to_offset(address_table_rva, sections)
        addresses, offsets = parse_import_address_table(address_table_offset, address_table_rva, optional_header, sections, data, offsets)
        
        import_entry["function_names"] = function_names
        import_entry["addresses"] = addresses
        
        if name:
            vals[name] = import_entry
        else:
            vals[current_offset] = import_entry
        offsets = build_import_offset_strings(import_entry, current_offset, name, offsets)
        current_offset += entry_len
        
        
    return vals, offsets
    

def parse_delay_import_table(dd, sections, optional_header, data, offsets):
    if not dd or "delay_import_table" not in dd:
        return None, offsets
    base_rva, table_len = dd["delay_import_table"]["virtual_address"], dd["delay_import_table"]["length"]
    if not base_rva or not table_len:
        return None, offsets
    
    base = rva_to_offset(base_rva, sections)
    if not base or base + table_len > len(data):
        return None, offsets

    vals = {}
    entry_len = struct.calcsize(delay_import_table_str)
    current_offset = base
    while current_offset - base < table_len and current_offset + entry_len < len(data):
        val_data = struct.unpack(delay_import_table_str, data[current_offset:current_offset+entry_len])
        check = 0
        for v in val_data:
            if v != 0:
                check = 1; break
        if not check:
            break
        import_entry = {}
        for offset, elem in enumerate(delay_import_table_spec):
            import_entry[elem[0]] = val_data[offset]
        name_rva = import_entry["name_rva"]
        if not name_rva:
            continue
        name, offsets = rva_string_lookup(name_rva, sections, optional_header["image_base"], data, offsets)
        lookup_table_rva = import_entry["delay_import_name_table"]
        lookup_table_offset = rva_to_offset(lookup_table_rva, sections)
        function_names, offsets = parse_import_lookup_table(lookup_table_offset, lookup_table_rva, optional_header, sections, data, offsets)
        address_table_rva = import_entry["delay_import_address_table"]
        address_table_offset = rva_to_offset(address_table_rva, sections)
        #Delay imports only have addresses in the file at the lookup table.  The address table is populated on demand in the image.
        addresses, offsets = parse_import_address_table(lookup_table_offset, address_table_rva, optional_header, sections, data, offsets)

        import_entry["function_names"] = function_names        
        import_entry["addresses"] = addresses   

        if name:
            vals[name] = import_entry
        else:
            vals[current_offset] = import_entry
        offsets = build_delay_offset_strings(import_entry, current_offset, name, offsets)
        current_offset +=  entry_len
        
    return vals, offsets

def build_import_offset_strings(imports, base, name, offsets):
    offset = base
    for elem in import_table_spec:
        len = elem[1]
        s = "%s - %s: %s (%s)"%(name, elem[0], imports[elem[0]], elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    return offsets


def build_delay_offset_strings(imports, base, name, offsets):
    offset = base
    for elem in delay_import_table_spec:
        len = elem[1]
        s = "%s - %s: %s (%s)"%(name, elem[0], imports[elem[0]], elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    return offsets
