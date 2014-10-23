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

logger = logging.getLogger('elf')

class elf_repr:
    def __init__(self, header):
        """ Initialize this object to have all of the members needed by the object_header
            module.
        """
        self.set_entry(header)
        self.set_image_version(header)
        self.set_machine(header)
        self.set_os_version(header)
        self.set_endian(header)
        self.set_imports(header)
        self.set_symbols(header)
        
        self.insn_mode = self.get_insn_mode(header)
        self.image_base = self.get_image_base(header)
        self.image_size = self.get_image_size(header)
        self.code_size = self.get_code_size(header)
        self.code_base = self.get_code_base(header)
        self.data_size = self.get_data_size(header)        
        self.section_info = self.get_section_info(header)
        self.section_names = self.section_info.keys()
 
        self.non_code_chunks = set() # Not sure how to do this for an ELF file
        self.file_alignment = "" # ELF has alignment for segments but not for the file as a whole
        self.linker_version = "" # ELF doesn't have this field
        self.data_base = 0 # ELF doesn't have this field
        self.delay_imports = None # ELF doesn't have delay imports
        

    
    def set_entry(self, header):
        self.entry = header["elf_header"]["entry"]
    
    def set_image_version(self, header):
        self.image_version = header["elf_header"]["version"] 
    
    def set_machine(self, header):
        self.machine = header["elf_header"]["machine"]
    
    def set_os_version(self, header):
        self.os_version = header["elf_header"]["osabi"]
    
    def set_endian(self, header):
        if header["elf_header"]["data"] == "ELFDATA2MSB":
            self.big_endian = True
            self.known_format = True
        elif header["elf_header"]["data"] == "ELFDATA2LSB":
            self.big_endian = False 
            self.known_format = True
        else:
            self.big_endian = None
            self.known_format = False
    
    def set_imports(self, header):   
        if "imports" in header:
            self.imports = header["imports"]
        else:
            self.imports = None
            
    def set_symbols(self, header):   
        if "symbols" in header:
            self.symbols = header["symbols"]
        else:
            self.symbols = None
    
    def get_section_info(self, header):
        """ Given an ELF header object return a sections object that conforms to the format
            used by the object_header module
        """
        sections = header["section_table"]
        if not sections:
            return {}
            
        section_info = {}
        for s in sections:
            section_info[s] = {}
            for e in sections[s]:
                if e == "offset":
                    section_info[s]["section_offset"] = sections[s][e]
                elif e == "addr":
                    section_info[s]["section_addr"] = sections[s][e]
                elif e == "size":
                    section_info[s]["section_len"] = sections[s][e]
                else:
                    section_info[s][e] = sections[s][e]
                    
            if "EXECINSTR" in sections[s]["flags"]:
                section_info[s]["section_exec"] = True
            else:
                section_info[s]["section_exec"] = False
                
        return section_info
        
    def get_entries(self):
        return [self.entry] # FIXME
        
    
    def get_non_code_chunks_of_section(self, section):
        return []  #FIXME
        
        
    def get_code_chunks_of_section(self, section):
        return [ (section["section_offset"], section["section_len"]) ] # FIXME
        
    
    def get_insn_mode(self, header):
        """ If this file is 32-bit return the integer 32,
            if this file is 64-bit return the integer 64,
            return None otherwise
        """
        insn_mode = None
        if header["elf_header"]["class"] == "32-bit":
            insn_mode = 32
        elif header["elf_header"]["class"] == "64-bit":
            insn_mode = 64
        else:
            insn_mode = None
        return insn_mode 
    
    def get_image_size(self, header):
        """ Return the cumulative size of the segments
        """
        size = 0
        for s in header["segments"]:
            size += header["segments"][s]["filesz"]
        return size
    
    def get_data_size(self, header):
        """ Return the cumulative size of the 'non-code' segments
        """
        size = 0
        segments = header["segments"]
        if not segments:
            return 0
        for s in segments:
            if "EXECUTE" not in segments[s]["flags"]:
                size += segments[s]["filesz"]
        return size    
    
    def get_code_size(self, header):
        """ Return the cumulative size of the 'code' segments
        """
        size = 0
        segments = header["segments"]
        if not segments:
            return 0
        for s in segments:
            if "EXECUTE" in segments[s]["flags"]:
                size += segments[s]["filesz"]
        return size
    
    def is_64bit(self):
        """ Return True if this file 64 bit and False otherwise
        """
        return self.insn_mode == 64

    def get_code_base(self, header):
        """ Return the starting address of the section where the entry point resides
        """
        entry = header["elf_header"]["entry"]
        sections = header["section_table"]
        if not sections:
            return 0
        for s in sections:
            beg = sections[s]["addr"]
            end = sections[s]["addr"] + sections[s]["size"] 
            if entry >= beg and entry < end:
                return beg
                
        return 0
        
    def get_image_base(self, header):
        """ first section address - first section offset
        """
        first_sec = None
        first_addr = None
        sections = header["section_table"]
        if not sections:
            return 0
            
        for name in sections:
            this_addr = sections[name]['addr']
            if first_sec == None or first_sec == '' or (this_addr != 0 and this_addr < first_addr):
                first_sec = name
                first_addr = this_addr 
        if not first_sec:
            return 0   # no sections found, call the image base 0.
        offset = sections[first_sec]['offset'] 
        addr = sections[first_sec]['addr']
        image_base = addr - offset
        return image_base
    
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
