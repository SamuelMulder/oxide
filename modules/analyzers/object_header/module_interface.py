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

desc = " This module retrieves the correct general header object from different file types."
name = "object_header"

import logging
import api, otypes

logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {"fake":{"type":bool, "mangle":False, "default":False}}

def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True }

def results(oid_list, opts):
    logger.debug("results()")
    if len(oid_list) != 1:
        logger.error("%s called incorrectly with an invalid list of IDs."%name)
    oid = oid_list[0]
    header = None
    src_type = api.get_field("src_type", oid, "type")
    if src_type == "PE":
        header = api.get_field("pe", oid, "header")
    elif src_type == "ELF":
        header = api.get_field("elf", oid, "header")
    elif src_type == "MACHO" or src_type == "OSX Universal Binary":
        header = api.get_field("macho", oid, "header")
        
    if opts["fake"] == True and header == None:
        data = api.get_field(api.source(oid), oid, "data")
        if data:
            header = fake_header(data)
            
    if not header:
        return None
    return {"header":header}
    
def fake_header(buf):
    class header:
        def get_code_chunks_of_section(section):
            return [(0, len(buf))]

    h = header()
    h.insn_mode = 32 # default - 32 bit
    h.known_format = False
    sections = {}
    sections["none"] = {}
    sections["none"]['section_exec'] = True
    sections["none"]['section_addr'] = 0
    sections["none"]['section_offset'] = 0
    sections["none"]['section_len'] = len(buf)
    sections["none"]['section_end'] = len(buf)
    h.section_info = sections
    return h
