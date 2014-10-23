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

logger = logging.getLogger('pe')

class pe_repr:
    def __init__(self, pe):
        self.big_endian   = False
        self.known_format = True
        
        # determine whether this is a 32 or 64 bit PE; condition TRUE => 64
        # can examine pe.FILE_HEADER.Machine or pe.FILE_HEADER.Characteristics
        if pe["coff_header"]:
            self.insn_mode = {False : 32,
                          True  : 64} [pe["coff_header"]["characteristics"]["32_BIT_MACHINE"] == 0] #pe.FILE_HEADER.Characteristics & 0x0100 == 0]
        else:
            self.insn_mode = 32
        
        if pe["optional_header"]:
            self.image_base = pe["optional_header"]["image_base"] #pe.OPTIONAL_HEADER.ImageBase
            self.image_size = pe["optional_header"]["size_of_image"] #pe.OPTIONAL_HEADER.SizeOfImage
            self.code_size = pe["optional_header"]["size_of_code"] #pe.OPTIONAL_HEADER.SizeOfCode
            self.code_base = pe["optional_header"]["base_of_code"] #pe.OPTIONAL_HEADER.BaseOfCode
            if "base_of_data" in pe["optional_header"]:
                self.data_base = pe["optional_header"]["base_of_data"] #pe.OPTIONAL_HEADER.BaseOfData
            else:
                self.data_base = 0
            self.file_alignment = pe["optional_header"]["file_alignment"] #pe.OPTIONAL_HEADER.FileAlignment
            self.image_version = str(pe["optional_header"]["major_image_version"]) + "." + \
                str(pe["optional_header"]["minor_image_version"])
            self.linker_version = str(pe["optional_header"]["major_linker_version"]) + "." + \
                str(pe["optional_header"]["minor_image_version"])
            self.os_version = str(pe["optional_header"]["major_os_version"]) + "." + \
                str(pe["optional_header"]["minor_os_version"])
        else:
            self.image_base = 0
            self.image_size = 0
            self.code_size = 0
            self.code_base = 0
            self.data_base = 0
            self.file_alignment = 1
            self.image_version = "N/A"
            self.linker_version = "N/A"
            self.os_version = "N/A"
          
        if "import_table" in pe:    
            self.imports = pe["import_table"]  #pe.DIRECTORY_ENTRY_IMPORT 
        else:
            self.imports = None
            
        if "delay_import_table" in pe:
            self.delay_imports = pe["delay_import_table"]
        else:
            self.delay_imports = None
            
        self.get_sections(pe)
        self.get_non_code_chunks(pe)

        self.get_entry_points(pe)
        self.get_symbols(pe)

    def get_sections (self, pe):
        self.section_info = dict()

        # image_base = 0
        # if (hasattr (pe, 'OPTIONAL_HEADER') and
        #     hasattr(pe.OPTIONAL_HEADER, 'ImageBase')):
        #     image_base = pe.OPTIONAL_HEADER.ImageBase
        
        # No valid section table.  Assume section is hiding in header, create fake section.
        if not "section_table" in pe or not pe["section_table"]:
            self.section_names = ["N/A"]
            self.section_info["N/A"] = \
                { 'section_offset'  : 0,
                  'section_addr'    : 0,
                  'section_len'     : self.image_size,
                  'section_end'     : self.image_size,
                  'section_exec'    : True }
            return
            
        names = dict()
        for n in pe["section_table"]: #pe.sections:
            s = pe["section_table"][n]
            offset = s["pointer_to_raw_data"]#pe.get_offset_from_rva(s["virtual_address"]) #s.VirtualAddress )
            name = s["name"]
            # make sure name is uniq; if not label it with an int
            if name in names: # is not uniq
                names[name] += 1
                fixed_name = "%s-dupe-%d" % (name, names[name])
                logger.warning ("duplicate section names in binary - '%s' renamed to '%s'",
                                name, fixed_name)
            else: # is uniq
                names[name] = 0
                fixed_name = name
            
            self.section_info [fixed_name] = \
                { 'section_offset' : offset,
                  'section_addr'   : s["virtual_address"],
                  'section_len'    : s["size_of_raw_data"],
                  'section_end'    : s["virtual_address"] + s["size_of_raw_data"],
                  'section_exec'   : s["characteristics"]["MEM_EXECUTE"] > 0 }

        self.section_names = self.section_info.keys()

                
    def get_non_code_chunks (self, pe):
        """
        This method is a first attempt to reflect that not all of an
        executable section might be code. Specifically, Microsoft compliers
        sometimes place the import tables in the .text section, which could
        cause us to disassemble a table unless we're careful.

        Here we add a list, "directories", to self. This list relays metadata
        on each non-empty directory.
        """
        def dir_in_exec_section(d):
            sec = self.find_section(d["virtual_address"])
            if not sec:
                return False
            return sec['section_exec']

        if not pe["optional_header"] or not pe["data_directories"]:
            return

        # build a list of tuples (directory_rva, directory_size)
        non_code_chunks = list()

        for n in pe["data_directories"]:
            d = pe["data_directories"][n]
            if d and dir_in_exec_section(d):
                non_code_chunks.append (dict(ofs = d["offset"],
                                             addr   = d["virtual_address"],
                                             len    = d["length"],
                                             end    = d["virtual_address"] + d["length"],
                                             name   = d["name"]))

        self.non_code_chunks = sorted (non_code_chunks,        # sorting based on offset
                                       lambda a,b: a['ofs']-b['ofs'])

        logger.debug("found these non-code chunks: %r", self.non_code_chunks)

    def get_entry_points(self, pe):
        addrs = set()
        if pe["optional_header"]:
            addrs.add(pe["optional_header"]["address_of_entry_point"])
        if "exports_directory_table" in pe and pe["exports_directory_table"]:
            for exp in pe["exports_directory_table"]["export_names"]: 
                addr = pe["exports_directory_table"]["export_names"][exp]
                addrs.add(addr)
        self.entry_addrs = addrs

    def get_symbols (self, pe):
        """
        Gets the import/delay import for a PE program
        """

        sym_tab = dict()
        
        if "import_table" in pe and pe["import_table"]:
            imps = pe["import_table"]
            for i in imps:
                if imps[i]["addresses"]:
                    for a in imps[i]["addresses"]:
                        sym_tab[a] = {'dll' : i,
                                  'name' : imps[i]["addresses"][a]}
            
        if "delay_import_table" in pe and pe["delay_import_table"]:
            imps = pe["delay_import_table"]
            for i in imps:
                if imps[i]["addresses"]:
                    for a in imps[i]["addresses"]:
                        sym_tab[a] = {'dll' : i,
                                  'name' : imps[i]["addresses"][a]}

        self.symbol_table = sym_tab

        
    def is_64bit (self):
        return (self.insn_mode == 64)
        
    def find_section(self, vaddr):
        for name in self.section_names:
            start = self.section_info[name]['section_addr']
            if vaddr < start: continue
            end = self.section_info[name]['section_end']
            if start <= vaddr < end:
                return self.section_info[name]
        return None

    def get_code_chunks_of_section(self, section):
        """
        Returns list of tuples (offset, len) of portions of section that are
        not found in self.non_code_chunks.
        """
        chunks = list()

        if not hasattr (self, 'non_code_chunks') or not self.non_code_chunks:
            return [ (section['section_offset'], section['section_len']) ]

        # self.non_code_chunks is sorted by offset
        last = section['section_offset']
        last_chunk_in_section = False

        section_start_ofs = section['section_offset']
        section_end_ofs   = section_start_ofs + section['section_len']
        logger.debug ("Section ranges [0x%x,0x%x]", section_start_ofs, section_end_ofs)
        
        for nx in self.non_code_chunks: # iter over "non-exec" chunks
            # is this chunk completely inside this section?
            logger.debug ("Is %r in section %r?", nx, section)
            
            if not (section['section_addr'] <= nx['addr'] and
                    nx['end'] <= section['section_end']      ):
                logger.debug ("no")
                last_chunk_in_section = False
                continue

            # this is a block of non-code in this section
            last_chunk_in_section = True
            
            # if "last" is before the start of this block, then record code block
            if last < nx['ofs']:
                chunk_len = nx['ofs'] - last
                chunks.append ( (last, chunk_len))
                logger.debug ("Adding (0x%x=%d, %d) as exec chunk",
                              last, last, chunk_len)
                #assert section_start_ofs <= last <= section_end_ofs, \
                #       "chunk doesn't start in section"
                #assert section_start_ofs <= last+chunk_len <= section_end_ofs, \
                #       "chunk doesn't end in section"

            # unconditionally advance last past block
            last = nx['ofs'] + nx['len'] 
            
        # add the end of the section, too
        if last_chunk_in_section:
            # chunk between last and end of section is code
            section_end_ofs = section['section_offset'] + section['section_len']
            chunk_size = section_end_ofs - last

            if chunk_size > 0:
                chunks.append ((last, section_end_ofs-last))
                assert section_start_ofs <= last <= section_end_ofs, \
                       "chunk doesn't start in section"
                assert section_start_ofs <= section_end_ofs <= section_end_ofs, \
                       "chunk doesn't end in section"
                
        logger.debug ("Found these code chunks: %r", chunks)
        return chunks
    
    def get_entries(self):
        return self.entry_addrs
            
    def get_offset(self, vaddr):
        """
        Returns physical offset of virtual address given.
        """
        offset = None
        info = self.find_section(vaddr)
        if info:
            offset = info['section_offset'] + (vaddr - info['section_addr'])
        if not offset:
            if vaddr > self.image_base:
                offset = self.get_offset(vaddr - self.image_base) # real virtual address, not relative
        return offset

    def get_rva(self, offset):
        """
        Returns relative virtual address of physical offset.
        """
        rva = None
        for n in self.section_names:
            ofs = self.section_info[n]['section_offset']
            end = ofs + self.section_info[n]['section_len']
            if ofs <= offset < end: # rva occurs in this section
                begin_va = self.section_info[n]['section_addr']
                rva = begin_va + (offset - ofs)
                break
        return rva
