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

import logging

logger = logging.getLogger('macho')

class universal_repr:
    def __init__(self, header):
        self.known_format = False
        
        self.set_magic(header)
        self.set_big_endian(header)
        self.set_num_embedded(header)
        self.set_embedded(header)
        self.section_info = []
        
    def set_magic(self, header):
        self.magic = header["magic"]
    
    def set_big_endian(self, header):
        self.big_endian = header["big_endian"]
        
    def set_num_embedded(self, header):
        self.num_embedded = header["nfat_arch"]
        
    def set_embedded(self, header):
        embedded = header["embedded"]
        self.embedded = []
        for f in embedded:
            self.embedded.append(macho_repr(f))

    def get_entries(self):
        return []         

class macho_repr:
    def __init__(self, header):
        """ Initialize this object to have all of the members needed by the object_header
            module.
        """
        self.known_format = True
        self.image_base = 0 #fixme
        self.image_size = 0 #fixme
        self.code_size = 0 #fixme
        self.code_base = 0 #fixme
        self.data_base = 0 #fixme
        self.file_alignment = 0 #fixme
        self.image_version = 0 #fixme
        self.linker_version = 0 #fixme
        self.os_version = 0 #fixme
        
        self.set_magic(header)
        self.set_insn_mode(header)
        self.set_machine(header)
        self.set_uuid(header)
        self.set_big_endian(header)
        self.set_header_offset(header)
        self.set_file_end(header)
        self.set_entries(header)
        self.set_imports(header)
        
        self.section_info = self.get_section_info(header)
        self.section_names = self.section_info.keys()
        
    def set_magic(self, header):
        self.magic = header["magic"]
    
    def set_insn_mode(self, header):
        self.insn_mode = header["addr_size"]

    def set_machine(self, header):
        self.machine = header["cputype"]

    def set_uuid(self, header):
        self.uuid = header["uuid"]
    
    def set_big_endian(self, header):
        self.big_endian = header["big_endian"]

    def set_header_offset(self, header):
        self.header_offset = header["header_offset"]
    
    def get_last_segment(self, header):
        last_segment_offset = 0
        last_segment_size = 0
        last_segment = None
        segments = header["segments"]
        for segment in segments:
            offset = segments[segment]["fileoff"]
            size = segments[segment]["filesize"]
            if offset > last_segment_offset:
                last_segment = segment
                last_segment_offset = offset
                last_segment_size = size 
                
        return last_segment
    
    def set_file_end(self, header):
        last_segment = self.get_last_segment(header)
        if last_segment is None:
            self.file_end = None
            return
    
        header_offset = header["header_offset"]
        last_segment_offset = header["segments"][last_segment]["fileoff"]
        last_segment_size = header["segments"][last_segment]["filesize"]
        
        self.file_end = header_offset + last_segment_offset + last_segment_size

    def set_entries(self, header):
        self.entries = [header["entry_point"]]
    
    def get_entries(self):
        return self.entries
    
    def get_section_info(self, header):
        """ Given a Macho-O header object return a sections object that conforms to the
            format used by the object_header module
        """
        section_info = {}
        segments = header["segments"]
        
        for seg in segments:
            for s in segments[seg]["sections"]:
                section_info[s] = {}
                
                section_info[s]["section_offset"] = segments[seg]["sections"][s]["offset"]
                section_info[s]["section_addr"] = segments[seg]["sections"][s]["addr"]
                section_info[s]["section_len"] = segments[seg]["sections"][s]["size"]
                
                flags = segments[seg]["sections"][s]["flags"]
                if ( "ATTR_PURE_INSTRUCTIONS" in flags or
                     "ATTR_SOME_INSTRUCTIONS" in flags or
                     "ATTR_SELF_MODIFYING_CODE" in flags):
                    section_info[s]["section_exec"] = True
                else:
                    section_info[s]["section_exec"] = False
                
        return section_info
            
    def get_insn_mode(self, header):
        return header["addr_size"]

    def set_image_version(self, header):
        self.image_version = 0 # FIXME 
    
    def set_os_version(self, header):
        self.os_version = "" # FIXME 
    
    def set_imports(self, header):
        self.imports = header["imports"]
                     
    def set_symbols(self, header):   
        self.symbols = "" # FIXME

    def get_non_code_chunks_of_section(self, section):
        return [] # FIXME
        
    def get_code_chunks_of_section(self, section):
        return [(section['section_offset'], section['section_len'])] # FIXME
        
    def get_image_size(self, header):
        return 0 # FIXME
    
    def get_data_size(self, header):
        return 0 # FIXME
    
    def get_code_size(self, header):
        return 0 # FIXME
    
    def is_64bit(self):
        return self.insn_mode == 64

    def get_code_base(self, header):
        return 0 # FIXME
        
    def get_image_base(self, header):
        return 0 # FIXME
    
    def find_section(self, vaddr):
        """ Given an address return the section that the address resides in
        """
        sections = self.section_info
        if not sections:
            return None
            
        for s in sections:
            beg = sections[s]["section_addr"]
            end = sections[s]["section_addr"] + sections[s]["section_len"] 
            if vaddr >= beg and vaddr <= end:
                return sections[s]
        return None
        
    def get_offset(self, vaddr):
        """
        Returns physical offset of virtual address given.
        """
        offset = None
        info = self.find_section(vaddr)
        if info:
            offset = info['section_offset'] + (vaddr - info['section_addr'])
        return offset

    def get_rva(self, offset):
        """
        Returns relative virtual address of physical offset.
        """
        rva = None
        for n in self.section_names:
            ofs = self.section_info[ n ]['section_offset']
            end = ofs + self.section_info[ n ]['section_len']
            if ofs <= offset < end: # rva occurs in this section
                begin_va = self.section_info[ n ]['section_addr']
                rva = begin_va + (offset - ofs)
                break
        return rva
