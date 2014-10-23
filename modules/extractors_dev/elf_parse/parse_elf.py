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

logger = logging.getLogger("parse_elf")

def parse_elf(data, oid):
    elf_header = parse_elf_header(data)
    if not elf_header:
        logger.warn("ELF Header not found in %s"%oid)
        return None

    header = {}
    header["elf_header"] = elf_header
    insn_mode = elf_header["class"]
    
    sections = parse_section_header(data, elf_header)
    header["section_table"] = sections

    segments = parse_program_header(data, elf_header)
    header["segments"] = segments

    if not sections:
        logger.warn("No sections found in %s"%oid)
        return header
    
    symbols, imports = parse_symbol_table(data, sections, elf_header)
    header["symbols"] = symbols
    header["imports"] = imports
    
    return header

                           
######################## ELF HEADER ######################################################
elf_ident_spec = [ 
    ("magic",       4, "File magic"),
    ("class",       1, "File class"),
    ("data",        1, "Data encoding"),
    ("version",     1, "File version"),
    ("osabi",       1, "Operating system and ABI"),
    ("abi_version", 1, "Version of the ABI"),
    ("pad",         6, "padding"),
    ("nident",      1, "Size of ident[]"),
]
elf_ident_str = "=4sBBBBB6BB"

elf_32_header_spec = [
    ("type",      2, "File type"),
    ("machine",   2, "Architecture"),
    ("version",   4, "File version"),
    ("entry",     4, "Starting virtual address, 0 if it doesn't exist"),
    ("phoff",     4, "Program header offset, 0 if it doesn't exist"),
    ("shoff",     4, "Section header offset, 0 if it doesn't exist"),
    ("flags",     4, "Processor specific flags"),
    ("ehsize",    2, "ELF header size in bytes"),
    ("phentsize", 2, "Size in bytes of program header"),
    ("phnum",     2, "Number of program header entries"),
    ("shentsize", 2, "Section header size in bytes"),
    ("shnum",     2, "Number of section header entries"),
    ("shstrndx",  2, "Section header table index"),
]
elf_32_header_str = "=HHLLLLLHHHHHH"

elf_64_header_spec = [
    ("type",      2, "File type"),
    ("machine",   2, "Architecture"),
    ("version",   4, "File version"),
    ("entry",     8, "Starting virtual address, 0 if it doesn't exist"),
    ("phoff",     8, "Program header offset, 0 if it doesn't exist"),
    ("shoff",     8, "Section header offset, 0 if it doesn't exist"),
    ("flags",     4, "Processor specific flags"),
    ("ehsize",    2, "ELF header size in bytes"),
    ("phentsize", 2, "Size in bytes of program header"),
    ("phnum",     2, "Number of program header entries"),
    ("shentsize", 2, "Section header size in bytes"),
    ("shnum",     2, "Number of section header entries"),
    ("shstrndx",  2, "Section header table index"),
]
elf_64_header_str = "=HHLQQQLHHHHHH"


def parse_elf_header(data):
    ident_len = struct.calcsize(elf_ident_str)
    if len(data) < ident_len:
        return None
    
    vals = {}
    val_data = struct.unpack(elf_ident_str, data[:ident_len])
    for offset, elem in enumerate(elf_ident_spec):
        vals[elem[0]] = val_data[offset]
    
    if vals["magic"] != "\x7fELF":
        return None

    vals["osabi"] = get_e_osabi(vals["osabi"])
    vals["class"] = get_e_class(vals["class"])

    elf_header_spec = elf_32_header_spec
    elf_header_str = elf_32_header_str
    if vals["class"] == "64-bit":
        elf_header_spec = elf_64_header_spec
        elf_header_str = elf_64_header_str
    
    header_len = struct.calcsize(elf_header_str)
    header_end = ident_len + header_len
    if len(data) < header_end:
        fill_len = header_end - len(data) 
        data += "\x00"*fill_len

    val_data = struct.unpack(elf_header_str, data[ident_len:header_end])
    for offset, elem in enumerate(elf_header_spec):
        vals[elem[0]] = val_data[offset]
   
    vals["machine"] = get_e_machine(vals["machine"])
    vals["type"] = get_e_type(vals["type"])
    vals["version"] = get_e_version(vals["version"])
    vals["data"] = get_e_data(vals["data"])
    
    return vals

def get_e_osabi(val):
    if val == 0:
        return "None specified"
    elif val == 1:
        return "HP-UX"
    elif val == 2:
        return "NetBSD"
    elif val == 3:
        return "GNU"
    elif val == 4:
        return "GNU/HURD"
    elif val == 5:
        return "86Open Common ABI"
    elif val == 6:
        return "Sun Solaris"
    elif val == 7:
        return "AIX"
    elif val == 8:
        return "IRIX"
    elif val == 9:
        return "FreeBSD"
    elif val == 10:
        return "Compaq TRU64 UINIX"
    elif val == 11:
        return "Novell Modesto"
    elif val == 12:
        return "Open BSD"
    elif val == 13:
        return "Open VMS"
    elif val == 14:
        return "HP Non-Stop Kernel"
    elif val == 15:
        return "Amiga Research OS"
    elif val == 16:
        return "FenixOS"
    elif val == 64:
        return "ARM specific"
    elif val == 97:
        return "ARM ABI"
    elif val == 255:
        return "Standalone"
    else:
        return "UNDEFINED"
    
def get_e_data(val):
    if val == 0:
        return "ELFDATANONE" # Unknown data format
    elif val == 1:
        return "ELFDATA2LSB" # Two's complement, little-endian
    elif val == 2:
        return "ELFDATA2MSB" # Two's complement, big-endian
    else:
        return "UNDEFINDED"

def get_e_version(val):
    if val == 0:
        return "Invalid version"
    elif val == 1:
        return "Current version"
    else:
        return "UNDEFINDED"
        
def get_e_type(val):
    if val == 0:
        return "No file type"
    elif val == 1:
        return "Relocatable file"
    elif val == 2:
        return "Executable file"
    elif val == 3:
        return "Shared object file"
    elif val == 4:
        return "Core file"
    elif val == 0xff00 or val == val == 0xffff:
        return "Processor-specific"        
    else:
        return "UNDEFINDED"

def get_e_machine(val):
    if val == 0:
        return "No machine"
    elif val == 1:
        return "AT&T WE 3210"
    elif val == 2:
        return "SPARC"
    elif val == 3:
        return "Intel 80386"
    elif val == 4:
        return "Motorola 68000"
    elif val == 5:
        return "Motorola 88000"
    elif val == 7:
        return "Intel 80860"
    elif val == 8:
        return "MIPS RS3000"
    elif val == 10:
        return "MIPS RS4 BE"
    elif val == 18:
        return "SPARC 32 Plus"
    elif val == 40:
        return "ARM"
    elif val == 41:
        return "Fake Alpha"
    elif val == 43:
        return "SPARCv9"
    elif val == 50:
        return "IA 64"
    elif val == 63:
        return "x86 64"
    else:
        return "UNDEFINED"
        

def get_e_class(val):
    if val == 0:
        return "Invalid class"
    elif val == 1:
        return "32-bit"
    elif val == 2:
        return "64-bit"
    else:
        return "UNDEFINDED"

def is64bit(elf_header):
    return elf_header["class"] == "64-bit"
    
    
######################## SECTIONS ########################################################
section_32_entry_spec = [
    ("name",      4, "Name of the section"),
    ("type",      4, "Section type"),
    ("flags",     4, "1-bit flags"),
    ("addr",      4, "Address of the first section's first byte"),
    ("offset",    4, "Offset from the first byte, or 0"),
    ("size",      4, "Section size in bytes"),
    ("link",      4, "Section header table index link"),
    ("info",      4, "Extra info"),
    ("addralign", 4, "Address alignment contraints, 0 otherwise"),
    ("entsize",   4, "Fixed-size entries"),
]
section_32_entry_str = "=LLLLLLLLLL"


section_64_entry_spec = [
    ("name",      4, "Name of the section"),
    ("type",      4, "Section type"),
    ("flags",     8, "1-bit flags"),
    ("addr",      8, "Address of the first section's first byte"),
    ("offset",    8, "Offset from the first byte, or 0"),
    ("size",      8, "Section size in bytes"),
    ("link",      4, "Section header table index link"),
    ("info",      4, "Extra info"),
    ("addralign", 8, "Address alignment contraints, 0 otherwise"),
    ("entsize",   8, "Fixed-size entries"),
]
section_64_entry_str = "=LLQQQQLLQQ"

def parse_section_header(data, elf_header):
    """ Section header is an array of entries ...
    
        There is a special entry elf_header["shstrndx"] that has the string table needed
        for section names
    """
    if elf_header["shoff"] == 0:
        print " No section header"
        return None
    
    if is64bit(elf_header):
        section_entry_str = section_64_entry_str
        section_entry_spec = section_64_entry_spec
    else:
        section_entry_str = section_32_entry_str
        section_entry_spec = section_32_entry_spec
    
    entry_len = struct.calcsize(section_entry_str)
    entries = {}
    offset = elf_header["shoff"]    
    for entry in range(elf_header["shnum"]):
        vals = {}
        if len(data) < offset+entry_len:
            break
        val_data = struct.unpack(section_entry_str, data[offset:offset+entry_len])    
        for i, elem in enumerate(section_entry_spec):
            vals[elem[0]] = val_data[i]            
        
        vals["flags"] = get_section_flags(vals["flags"])
        vals["type"] =  get_section_type(vals["type"])
        
        entries[entry] = vals
        offset += entry_len
        
    if not entries:
        return {}
    
    sections = assign_section_names(data, entries, elf_header["shstrndx"])
    return sections


def get_name_from_string_table(data, st_offset, index):
    if index == 0:
        return None
    i = st_offset + index
    name = ""
    try:
        while data[i] != "\x00": # Names are null terminated
            name += data[i]
            i+=1
    except IndexError:
        print " Out of bounds while searching string table"
        return None
        
    return name
    
def assign_section_names(data, entries, st_entry):
    if not entries:
        return {}  
    offset = entries[st_entry]["offset"] # offset to the string table section
    sections = {}
    for e in entries:
        name = get_name_from_string_table(data, offset, entries[e]["name"])
        if name is not None:
            sections[name] = entries[e]        
    return sections
    
def get_section_flags(val):
    if val == 0x0:
        return []

    flags = []
    if val & 0x1:
        flags.append("WRITE")
    if val & 0x2:
        flags.append("ALLOC")
    if val & 0x4:
        flags.append("EXECINSTR")
    if val == 0xf000000:
        flags.append("MASKPROC")
    return flags

def get_section_type(val):
    if val == 0:
        return "NULL"
    elif val == 1:
        return "PROGBITS"
    elif val == 2:
        return "SYMTAB"
    elif val == 3:
        return "STRTAB"
    elif val == 4:
        return "RELA"
    elif val == 5:
        return "HASH"
    elif val == 6:
        return "DYNAMIC"
    elif val == 7:
        return "NOTE"
    elif val == 8:
        return "NOBITS"
    elif val == 9:
        return "REL"
    elif val == 10:
        return "SHLIB"
    elif val == 11:
        return "DYNSYM"
    elif val == 0x70000000:
        return "LOPROC"
    elif val == 0x7fffffff:
        return "HIPROC"
    elif val == 0x80000000:
        return "LOUSER"
    elif val == 0xffffffff:
        return "HIUSER"
    else:  
        return "UNDEFINED"
        
######################## PROGRAM HEADER ##################################################
segment_32_entry_spec = [
    ("type",   4, "Type of segment"),
    ("offset", 4, "Offset from begining of the file"),
    ("vaddr",  4, "Virtual address of the segment"),
    ("paddr",  4, "Physical address of the segment"),
    ("filesz", 4, "File image size in bytes"),
    ("memsz",  4, "Memory image size in bytes"),
    ("flags",  4, "Flags"),
    ("align",  4, "Segment alignment in memory and in the file"),

]
segment_32_entry_str = "=LLLLLLLL"

segment_64_entry_spec = [
    ("type",   4, "Type of segment"),
    ("flags",  4, "Flags"),
    ("offset", 8, "Offset from begining of the file"),
    ("vaddr",  8, "Virtual address of the segment"),
    ("paddr",  8, "Physical address of the segment"),
    ("filesz", 8, "File image size in bytes"),
    ("memsz",  8, "Memory image size in bytes"),
    ("align",  8, "Segment alignment in memory and in the file"),

]
segment_64_entry_str = "=LLQQQQQQ"

def parse_program_header(data, elf_header):
    """ Program header is an array of entries ...
    """
    if elf_header["phoff"] == 0:
        print " No program header"
        return None

    if is64bit(elf_header):
        segment_entry_str = segment_64_entry_str
        segment_entry_spec = segment_64_entry_spec
    else:
        segment_entry_str = segment_32_entry_str
        segment_entry_spec = segment_32_entry_spec        

    entry_len = struct.calcsize(segment_entry_str)
    offset =  elf_header["phoff"]    
    segments = {}
    for entry in range(elf_header["phnum"]):
        vals = {}
        val_data = struct.unpack(segment_entry_str, data[offset:offset+entry_len])    
        for i, elem in enumerate(segment_entry_spec):
            vals[elem[0]] = val_data[i]            
        
        vals["type"] = get_segment_type(vals["type"])
        vals["flags"] = get_segment_flags(vals["flags"])
        
        segments[entry] = vals
        offset += entry_len
        
    return segments
        
def get_segment_flags(val):
    if val == 0x0:
        return []
        
    flags = []
    if val & 0x1:
        flags.append("EXECUTE")
    if val & 0x2:
        flags.append("WRITE")
    if val & 0x3:
        flags.append("READ")
    return flags        

def get_segment_type(val):
    if val == 0:
        return "NULL"
    elif val == 1:
        return "LOAD"
    elif val == 2:
        return "DYNAMIC"
    elif val == 3:
        return "INTERP"
    elif val == 4:
        return "NOTE"
    elif val == 5:
        return "SHLIB"
    elif val == 6:
        return "PHDR"
    elif val == 0x7000000:
        return "LOPROC"
    elif val == 0x7fffffff:
        return "HIPROC"
        
######################## SYMBOL TABLE ####################################################
symbol_32_entry_spec = [
    ("name",  4, "Symbol name"),
    ("value", 4, "Value of the symbol, may be absolute or an address or ..."),
    ("size",  4, "Size of the symbol, may be 0"),
    ("info",  1, "Type and binding attributes"),
    ("other", 1, "No meaning, should be 0"),
    ("shndx", 2, "Section header table index for the symbol"),
]
symbol_32_entry_str = "=LLLBBH"

symbol_64_entry_spec = [
    ("name",  4, "Symbol name"),
    ("info",  1, "Type and binding attributes"),
    ("other", 1, "No meaning, should be 0"),
    ("shndx", 2, "Section header table index for the symbol"),
    ("value", 8, "Value of the symbol, may be absolute or an address or ..."),
    ("size",  8, "Size of the symbol, may be 0"),
]
symbol_64_entry_str = "=LBBHQQ"

def parse_symbol_table(data, sections, elf_header):
    """ Symbol table is an array of entries ...
    """
    if is64bit(elf_header):
        symbol_entry_str = symbol_64_entry_str
        symbol_entry_spec = symbol_64_entry_spec
    else:
        symbol_entry_str = symbol_32_entry_str
        symbol_entry_spec = symbol_32_entry_spec
    entry_len = struct.calcsize(symbol_entry_str)
    
    st_offset = None
    if ".symtab" in sections:
        section = ".symtab"
        if ".strtab" in sections:
            st_offset = sections[".strtab"]["offset"]
        else:
            st_offset = sections[section]["offset"]
        
    elif ".dynsym" in sections:
        section = ".dynsym"
        if ".dynstr" in sections:
            st_offset = sections[".dynstr"]["offset"]
        else:
            st_offset = sections[section]["offset"]
    
        
    if section not in sections:
        return {}, {} 
        
    symbols = {}
    imports = {}
    offset = sections[section]["offset"]
    size = sections[section]["size"]
    index = offset
    while index < offset + size:
        vals = {}
        if len(data) < index+entry_len: 
            break
            
        val_data = struct.unpack(symbol_entry_str, data[index:index+entry_len])
        for i, elem in enumerate(symbol_entry_spec):
            vals[elem[0]] = val_data[i]
        
        if st_offset is None:
            symbols[vals["name"]] = vals
        else:
            func_name = get_name_from_string_table(data, st_offset, vals["name"])
            if func_name:
                vals.pop("name")
                vals["info"] = get_symbol_info(vals["info"])
                vals["shndx"] = get_symbol_shndx(vals["shndx"])
                
                if vals["info"] == "UNDEFINED" and vals["value"] == 0:
                    tmp_name = func_name
                    import_name = "Unknown"
                    if "@@" in func_name:
                        i = tmp_name.find("@@")
                        func_name = tmp_name[:i]
                        import_name = tmp_name[i:].strip("@@") 
                    if import_name not in imports:
                        imports[import_name] = {}
                    imports[import_name][func_name] = vals
                symbols[func_name] = vals
                
        index += entry_len  
                  
    return symbols, imports
         
def get_symbol_info(val):
    if val == 0:
        return "NOTYPE"
    elif val == 1:
        return "OBJECT"
    elif val == 2:
        return "FUNC"
    elif val == 3:
        return "SECTION"
    elif val == 4:
        return "FILE"
    elif val == 13:
        return "LOPROC"
    elif val == 15:
        return "HIPROC"
    else:
        return "UNDEFINED"
         
def get_symbol_shndx(val):
    if val == 0:
        return "LOCAL"
    elif val == 1:
        return "GLOBAL"
    elif val == 2:
        return "WEAK"
    elif val == 13:
        return "LOPROC"
    elif val == 14:
        return "HIPROC"
    else:
        return str(val)
