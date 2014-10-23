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

desc = " This module parses PE files."
name = "pe_parse"

from collections import defaultdict
import logging
from parse_dos import parse_dos_header
from parse_coff import parse_coff_header, parse_pe_signature
from parse_opt import parse_optional_header_fixed, parse_section_header_table, parse_data_directory
from parse_certs import parse_certificate_table
from parse_imports import parse_import_table, parse_delay_import_table
from parse_relocs import parse_base_relocations
from parse_exports import parse_exports_directory_table
import api


logger = logging.getLogger(name)
logger.debug("init")

opts_doc = {}

def documentation():
    return {"description":desc, "opts_doc":opts_doc, "set":False, "atomic":True }

def process(oid, opts):
    logger.debug("process()")
    src_type = api.get_field("src_type", oid, "type")
    if src_type != "PE" and src_type != "ZM":
        return False
    src = api.source(oid)
    data = api.get_field(src, oid, "data")
    if not data: 
        logger.debug("Not able to process %s",oid)
        return False
    result = parse_pe(data, oid)
        
    if result:
        api.store(name, oid, result, opts)
        return True
    return False
    
def parse_pe(data, file_id):
    header = {}
    header["dos_header"] = None
    header["coff_header"] = None
    header["optional_header"] = None
    header["offsets"] = defaultdict(list)
    
    global oid 
    oid = file_id
    dos_header, header["offsets"] = parse_dos_header(data, header["offsets"])
    if not dos_header:
        logger.warn("DOS Header not found in %s"%oid)
        return None
    header["dos_header"] = dos_header
    
    pe_sig_offset = dos_header["lfanew"]
    pe_signature, header["offsets"] = parse_pe_signature(pe_sig_offset, data, header["offsets"])
    if not pe_signature:
        logger.warn("PE signature not found in %s"%oid)
        return header
    header["pe_signature"] = pe_signature
    
    pe_base = pe_sig_offset + len(pe_signature)
    coff_header, header["offsets"] = parse_coff_header(pe_base, data, header["offsets"])
    if not coff_header:
        return header
    header["coff_header"] = coff_header

    optional_header, data_directory_offset, header["offsets"] = parse_optional_header_fixed(pe_base, data, header["offsets"])
    header["optional_header"] = optional_header
    if not header["optional_header"]:
        logger.warn("Optional header not found in %s"%oid)
        return header
    if not data_directory_offset:
        logger.warn("Section table not found in %s"%oid)
        return header
        
    section_table, header["offsets"] = parse_section_header_table(coff_header, pe_base, data, header["offsets"])
    if section_table:
        for s in section_table:
            if optional_header["file_alignment"] and section_table[s]["pointer_to_raw_data"] % optional_header["file_alignment"]:
                logger.warn("Misaligned section in %s"%oid)
    
    header["section_table"] = section_table

    dd, header["offsets"] = parse_data_directory(data_directory_offset, section_table, optional_header, data, header["offsets"])
    header["data_directories"] = dd

    certificate_table, header["offsets"] = parse_certificate_table(dd, data, header["offsets"])
    header["certificate_table"] = certificate_table

    import_table, header["offsets"] = parse_import_table(dd, section_table, optional_header, data, header["offsets"])
    header["import_table"] = import_table
    
    delay_import_table, header["offsets"] = parse_delay_import_table(dd, section_table, optional_header, data, header["offsets"])
    header["delay_import_table"] = delay_import_table

    relocs, header["offsets"] = parse_base_relocations(dd, section_table, data, header["offsets"])
    header["relocations"] = relocs

    exports, header["offsets"] = parse_exports_directory_table(dd, section_table, optional_header, data, header["offsets"])
    header["exports_table"] = exports

    return header
"""
    
    header["resources"] = parse_resource_directory(dd, section_table, optional_header, data)
    
"""
###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################
