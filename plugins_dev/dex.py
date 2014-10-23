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


import api

def dex_header(args, opts):
    """ Plugin: Prints the header for a dex file
        Syntax: dex_header %<oid> ...
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    
    oids = api.expand_oids(valid)
    for oid in oids:
        print_dex_header(oid)
    return oids

exports = [dex_header]

############## UTILS #########################################################
def print_dex_header(oid):
    dex = api.retrieve("dex_parse", oid)
    if not dex:
        print "  - %s does not have a valid dex header" % (oid)
        return

    header = dex["header"]
    print "  oid: %s" % (oid)
    print "  DEX version %s" % (dex["version"])
    print "  Reverse endian: %s" % (dex["reverse_endian"])
    print "  DEX file header:"
    print "    magic:",
    print_magic(header["magic"])
            
    print "    checksum: %s" % (hex(header["checksum"]))
    print "    signature (SHA1): ",
    print_signature(header["signature"])

    print "    file_size: %s" % (header["file_size"])
    print "    header_size: %s (%s)" % (header["header_size"], hex(header["header_size"]))
    print "    endian_tag: %s (%s)" % (header["endian_tag"], hex(header["endian_tag"]))

    print "    link_size: %s" % (header["link_size"])
    print "    link_off: %s (%s)" % (header["link_off"], hex(header["link_off"]))
    
    print "    map_off: %s (%s)" % (header["map_off"], hex(header["map_off"]))

    print "    string_ids_size: %s" % (header["string_ids_size"])
    print "    string_ids_off: %s (%s)" % (header["string_ids_off"], hex(header["string_ids_off"]))
            
    print "    type_ids_size: %s" % (header["type_ids_size"])
    print "    type_ids_off: %s (%s)" % (header["type_ids_off"], hex(header["type_ids_off"]))
            
    print "    field_ids_size: %s" % (header["field_ids_size"])
    print "    field_ids_off: %s (%s)" % (header["field_ids_off"], hex(header["field_ids_off"]))
            
    print "    method_ids_size: %s" % (header["method_ids_size"])
    print "    method_ids_off: %s (%s)" % (header["method_ids_off"], hex(header["method_ids_off"]))
            
    print "    class_defs_size: %s" % (header["class_defs_size"])
    print "    class_defs_off: %s (%s)" % (header["class_defs_off"], hex(header["class_defs_off"]))
            
    print "    data_size: %s" % (header["data_size"])
    print "    data_off: %s (%s)" % (header["data_off"], hex(header["data_off"]))
    
    print
    print_map_list(dex["map_list"])
    
    
def print_map_list(map_list):
    print "  Map List:"
    for i in map_list:
        print "    type: %s    offset: %s (%s)    size: %s" % (i["type"], i["offset"], hex(i["offset"]), i["size"]) 
    print
    
    
def print_magic(magic):
    s = ""
    for v in magic:
        if v == "\n":
            s += "\\n"
        elif v =="\x00":
            s += "\\x00"
        else:
            s += chr(ord(v))
    print s

                
def print_signature(signature):
    s = ""
    for v in signature:
        s += hex(ord(v)).replace("0x", "")
    print s 
