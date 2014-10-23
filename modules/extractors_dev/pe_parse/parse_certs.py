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

logger = logging.getLogger("parse_certs")

# (name, offset, desc)
certificate_table_spec = [
    ("length", 4, "Length of the certificate"),
    ("revision", 2, "Certificate version number"),
    ("type", 2, "Type of the content"),
  ]
certificate_table_str = "=LHH"

def parse_certificate_table(dd, data, offsets):
    if not dd or "certificate_table" not in dd:
        return None, offsets
    base, table_len = dd["certificate_table"]["offset"], dd["certificate_table"]["length"]
    if base == 0 and table_len == 0:
        return None, offsets
    if base + table_len > len(data):    
        return None, offsets
    vals = []
    entry_len = struct.calcsize(certificate_table_str)
    current_offset = base
    while current_offset - base < table_len and current_offset + entry_len < len(data):
        certificate = {}
        val_data = struct.unpack(certificate_table_str, data[current_offset:current_offset+entry_len])
        for offset, elem in enumerate(certificate_table_spec):
            certificate[elem[0]] = val_data[offset]
        length = certificate["length"]
        if not length:
            break
        if current_offset + length < len(data):
            certificate["data"] = data[current_offset+entry_len:current_offset+length] 
        else:
            certificate["data"] = None
        offsets[current_offset] = [{"len":length, "string":"Certificate"}]
        if length % 8 > 0:
            length += 8 - (length % 8)
        current_offset +=  length 
        vals.append(certificate)
    return vals, offsets
                              
