
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

""" DEX Spec: http://source.android.com/tech/dalvik/dex-format.html
"""

import struct, logging
import api

logger = logging.getLogger("parse_dex")
image_dos_header_spec = None

ENDIAN_CONSTANT = 0x12345678;
REVERSE_ENDIAN_CONSTANT = 0x78563412;


def parse_dex(data, fid):
    dex = {}
    global oid 
    oid = fid
    
    header = parse_dex_header(data)    
    if not header:
        logger.warn("DEX Header not found in %s"%oid)
        return None
  
    dex["header"] = header
    dex["version"] = str(dex["header"]["magic"][4:7])
    
    if hex(header["endian_tag"]) == hex(REVERSE_ENDIAN_CONSTANT):
        dex["reverse_endian"] = True
    elif hex(header["endian_tag"]) == hex(ENDIAN_CONSTANT):    
        dex["reverse_endian"] = False
    else:
        dex["reverse_endian"] = None
    
    map_data = data[header["map_off"]:]
    dex["map_list"] = parse_map_list(map_data)
    
    return dex


dex_header_spec = [ 
    ("magic", 8, "magic number, dex\n035\0 where 035 is the version"),
    ("checksum", 4, "adler32 checksum of the rest of the file"),
    ("signature", 20, "SHA-1 of the rest of the file ("),
                   
    ("file_size", 4, "size of the entire file"),
    ("header_size", 4, "size of the header (this entire section), in bytes"),
    ("endian_tag", 4, "endianness tag"),
                   
    ("link_size", 4, "size of the link section, or 0 if this file isn't statically linked"),
    ("link_off", 4, "offset from the start of the file to the link section, or 0 if link_size is 0"),
                   
    ("map_off", 4, "offset from the start of the file to the map item, or 0 if this file has no map"),
                   
    ("string_ids_size", 4, "count of strings in the string identifiers list"),
    ("string_ids_off", 4, "offset from the start of the file to the string identifiers list, or 0 if string_ids_size is 0"),

    ("type_ids_size", 4, "count of elements in the type identifiers list"),
    ("type_ids_off", 4, "offset from the start of the file to the type identifiers list, or 0 if type_ids_size is 0"),
                   
    ("proto_ids_size", 4, "count of elements in the prototype identifiers list"),
    ("proto_ids_off", 4, "offset from the start of the file to the prototype identifiers list, or 0 if proto_ids_size is 0"),
                   
    ("field_ids_size", 4, "count of elements in the field identifiers list"),
    ("field_ids_off", 4, "offset from the start of the file to the field identifiers list, or 0 if field_ids_size is 0"),
                   
    ("method_ids_size", 4, "count of elements in the method identifiers list"),
    ("method_ids_off", 4, "offset from the start of the file to the method identifiers list, or 0 if method_ids_size is 0"),
                   
    ("class_defs_size", 4, "count of elements in the class definitions list"),
    ("class_defs_off", 4, "offset from the start of the file to the class definitions list, or 0 if class_defs_size is 0"),
                   
    ("data_size", 4, "	Size of data section in bytes. Must be an even multiple of sizeof(uint)."),
    ("data_off", 4, "offset from the start of the file to the start of the data section"),
]
dex_header_str = "=8sL20sLLLLLLLLLLLLLLLLLLLL"

def parse_dex_header(data):
    vals = {}
    spec_len = struct.calcsize(dex_header_str)
    if len(data) < spec_len:
        return None
    
    val_data = struct.unpack(dex_header_str, data[:spec_len])
    for offset, elem in enumerate(dex_header_spec):
        vals[elem[0]] = val_data[offset]
    
    return vals


def convert_map_type(value, size):
    if hex(value) == hex(0x0000):
        return ("header_item", 0x70)
    elif hex(value) == hex(0x0001):
        return ("string_id_item", 0x04)
    elif hex(value) == hex(0x0002):
        return ("type_id_item", 0x04)
    elif hex(value) == hex(0x0003):
        return ("proto_id_item", 0x0c)
    elif hex(value) == hex(0x0004):
        return ("field_id_item", 0x08)
    elif hex(value) == hex(0x0005):
        return ("method_id_item", 0x08)
    elif hex(value) == hex(0x0006):
        return ("class_def_item", 0x20)
    elif hex(value) == hex(0x1000):
        return ("map_list", 4 + size * 12)
    elif hex(value) == hex(0x1001):
        return ("type_list", 4 + size * 2)
    elif hex(value) == hex(0x1002):
        return ("annotation_set_ref_list", 4 + size * 4)
    elif hex(value) == hex(0x1003):
        return ("annotation_set_item", 4 + size * 4)
    elif hex(value) == hex(0x2000):
        return ("class_data_item", 0)
    elif hex(value) == hex(0x2001):
        return ("code_item", 0)
    elif hex(value) == hex(0x2002):
        return ("string_data_item", 0)
    elif hex(value) == hex(0x2003):
        return ("debug_info_item", 0)
    elif hex(value) == hex(0x2004):
        return ("annotation_item", 0)
    elif hex(value) == hex(0x2005):
        return ("encoded_array_item", 0)
    elif hex(value) == hex(0x2006):
        return ("annotations_directory_item", 0)
    else:
        return ("invalid", -1)

map_item_spec = [
    ("type", 2, "type of the items"),
    ("unused", 2, "unused"),
    ("size", 4, "count of the number of items found at the offset"),
    ("offset", 4, "offset from the start of the file to the items"),  
]
map_item_str = "=HHLL"

def parse_map_item(data):
    vals = {}
    spec_len = struct.calcsize(map_item_str)
    if len(data) < spec_len:
        return None
    
    val_data = struct.unpack(map_item_str, data[:spec_len])
    for offset, elem in enumerate(map_item_spec):
        vals[elem[0]] = val_data[offset]
        
    t, s = convert_map_type(vals["type"], vals["size"])
    vals["type"] = t
    vals["size"] = s
        
    return vals


def parse_map_list(map_data):
    size = struct.unpack("=L", map_data[:4])[0] 
    map_item_len = struct.calcsize(map_item_str)
    map_list = []
    i = 0
    while i < size:
        map_item_data = map_data[4+i*map_item_len:]
        map_list.append(parse_map_item(map_item_data))
        i += 1
        
    return map_list
    

########### FIXME ##########

method_id_item_spec = [
    ("class_idx", 2, "index into the type_ids list for the definer of this method. This must be a class or array type, and not a primitive type. "),
    ("proto_idx", 2, "index into the proto_ids list for the prototype of this method "),
    ("name_idx", 4, "index into the string_ids list for the name of this method. The string must conform to the syntax for MemberName"),

]
method_id_item_str = "=HHL"


class_def_item_spec = [
    ("classs_idx", 4, ""),
    ("access_flags", 4, ""),
    ("superclass_idx", 4, ""),
    ("interfaces_off", 4, ""),
    ("source_file_idx", 4, ""),
    ("annotations_off", 4, ""),
    ("class_data_off", 4, ""),
    ("static_values_off", 4, ""),    
]
class_def_item_str = "=LLLLLLLL"

#class_data_item_spec = [
#    ("", uleb128, ""), # FIXME: need to figure out how to parse this type
#]
    
