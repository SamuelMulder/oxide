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

logger = logging.getLogger("parse_dos")

# (name, length, desc)
image_dos_header_spec = [ ("magic", 2, "magic number"),
    ("cblp", 2, "Bytes on last page of file"),
    ("cp", 2, "Pages in file"),
    ("crlc", 2, "Relocations"),
    ("cparhdr", 2, "Size of header in paragraphs (should be 4)"),
    ("minalloc", 2, "Minimum extra paragraphs needed"),
    ("maxalloc", 2, "Maximum extra paragraphs needed"),
    ("ss", 2, "Initial relative ss value"),
    ("sp", 2, "Inital sp value"),
    ("csum", 2, "Checksum"),
    ("ip", 2, "Inital ip value"),
    ("cs", 2, "Inital relative cs value"),
    ("lfarlc", 2, "File address of relocation table"),
    ("ovno", 2, "Overlay number"),
    ("res", 8, "Reserved words"),
    ("oemid", 2, "OEM identifier"),
    ("oeminfo", 2, "OEM information"),
    ("res2", 20, "Reserved words"),
    ("lfanew", 4, "File address of new exe header")
  ]
image_dos_header_str = "=2sHHHHHHHHHHHHH8sHH20sL"
                              
def parse_dos_header(data, offsets):
    vals = {}
    spec_len = struct.calcsize(image_dos_header_str)
    if len(data) < spec_len:
        logger.warn("DOS Header not found")
        return None
    val_data = struct.unpack(image_dos_header_str, data[:spec_len])
    for offset, elem in enumerate(image_dos_header_spec):
        vals[elem[0]] = val_data[offset]
    if vals["magic"] != "MZ" and vals["magic"] != "ZM":
        logger.warn("DOS Signature not found")
        return None
    offsets = build_offset_strings(vals, 0, offsets)
    
    vals['dos_stub'], header_len, stub_len = parse_dos_stub(vals, data)
    if stub_len:
        offsets[header_len].append({"len":stub_len, "string": "dos_stub"})
        offsets = parse_rich_signature(vals, offsets)
    return vals, offsets
    
def parse_dos_stub(dos_header, data):
    header_len = struct.calcsize(image_dos_header_str)
    dos_stub_offset = dos_header["cparhdr"] * 16
    if dos_stub_offset != header_len:
        logger.warn("Unusual cparhdr value pointing to DOS header")
    lfanew = dos_header["lfanew"]
    dos_stub_len = lfanew-header_len
    if dos_stub_len > 0:
        return data[dos_stub_offset:lfanew], header_len, dos_stub_len
    else:
        return None, header_len, 0
        
def parse_rich_signature(dos_header, offsets):
    dos_stub = dos_header['dos_stub']
    if len(dos_stub) <= 64 + 1024:
        return offsets
    else:
        rich_sig = dos_stub[64:]
    #algorithm adapted from http://ntcore.com/files/richsign.htm
    n_sign_dwords = 0
    for i in xrange(100):
        dw = struct.unpack("=L", rich_sig[i*4:(i*4)+4])[0]
        if dw == 0x68636952:
            n_sign_dwords = i
            break
    if not n_sign_dwords:
        return offsets
    mask = struct.unpack("=L", rich_sig[(n_sign_dwords+1)*4: (n_sign_dwords+1)*4 + 4])[0]
    str_info = "Rich Signature - VC++ tools used: "
    for i in xrange(4, n_sign_dwords, 2):
        dw = struct.unpack("=L", rich_sig[i*4:i*4+4])[0] ^ mask
        id = dw >> 16
        minver = dw & 0xFFFF
        vnum = struct.unpack("=L", rich_sig[(i+1)*4:(i+1)*4+4])[0] ^ mask
        str_info = str_info + ": ID: " + str(id) + ", Version: " + str(minver) + " Times: " + str(vnum)
    offsets[0x80].append({ "string": str_info, "len":n_sign_dwords*4 })
    dos_header["rich_signature"] = str_info
    return offsets
    
    
def build_offset_strings(dos_header, base, offsets):
    offset = base
    for elem in image_dos_header_spec:
        len = elem[1]
        if len > 4:
            s = "%s (%s)"%(elem[0], elem[2])
        else:
            s = "%s: %s  (%s)"%(elem[0], dos_header[elem[0]], elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    return offsets