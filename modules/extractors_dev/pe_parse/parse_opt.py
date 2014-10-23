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

logger = logging.getLogger("parse_opt")

image_optional_header_base_spec = [
    ("magic_type", 2, "0x10B = normal EXE, 0x107 = ROM image, 0x20B = PE32+ (64bit0)"),
    ("major_linker_version", 1, "Linker major version number"),
    ("minor_linker_version", 1, "Linker minor version number"),
    ("size_of_code", 4, "Size of code section or sum of all code sections if multiple"),
    ("size_of_initialized_data", 4, "Size of initialized data section or sum if multiple"),
    ("size_of_uninitialized_data", 4, "Size of uninitialized data section (BSS) or sum if multiple"),
    ("address_of_entry_point", 4, "RVA to entry of executable, init function for device drivers, and optional for dlls"),
    ("base_of_code", 4, "RVA to base of code section"),
  ]
image_optional_header_base_str = "=HBBLLLLL"

image_optional_header_pe32_spec = [
    ("base_of_data", 4, "RVA to beginning of data section"),
    ("image_base", 4, "Preferred aaddress of image when loaded"),
    ("section_alignment", 4, "Alignment of sections in bytes when loaded into memory, >= file_alignment"),
    ("file_alignment", 4, "Alignment of sections in bytes in the image file (default is 512)"),
    ("major_os_version", 2, "OS major version number"),
    ("minor_os_version", 2, "OS minor version number"),
    ("major_image_version", 2, "Image major version number"),
    ("minor_image_version", 2, "Image minor version number"),
    ("major_subsystem_version", 2, "Subsystem major version number"),
    ("minor_subsystem_version", 2, "Subsystem minor version number"),
    ("win32_version", 4, "Reserved, must be 0"),
    ("size_of_image", 4, "Size of bytes in image as loaded in memory, must be multiple of section_alignment"),
    ("size_of_headers", 4, "Combined size of DOS Stub, PE header, and Section headers, rounded to multiple of file_alignment"),
    ("checksum", 4, "Image file checksum as computed by imaghelp.dll"),
    ("subsystem", 2, "Subsystem rquired to run, see subsytem_description"),
    ("dll_characteristics", 2, "DLL characteristics - see boolean values"),
    ("size_of_stack_reserve", 4, "Memory reserved for stack"),
    ("size_of_stack_commit", 4, "Memory initially commited for the stack, additional pages added as needed"),
    ("size_of_heap_reserve", 4, "Memory reserved for local heap"),
    ("size_of_heap_commit", 4, "Memory initially commited for the local heap, additional pages added as needed"),
    ("loader_flags", 4, "Reserved - must be 0"),
    ("number_of_data_directories", 4, "Number of data directory entries following"),
  ]
image_optional_header_pe32_str = "=LLLLHHHHHHLLLLHHLLLLLL"

image_optional_header_pe32_plus_spec = [
    ("image_base", 8, "Preferred address of image when loaded"),
    ("section_alignment", 4, "Alignment of sections in bytes when loaded into memory, >= file_alignment"),
    ("file_alignment", 4, "alignment of sections in bytes in the image file (default is 512)"),
    ("major_os_version", 2, "OS major version number"),
    ("minor_os_version", 2, "OS minor version number"),
    ("major_image_version", 2, "Image major version number"),
    ("minor_image_version", 2, "Image minor version number"),
    ("major_subsystem_version", 2, "Subsystem major version number"),
    ("minor_subsystem_version", 2, "Subsystem minor version number"),
    ("win32_version", 4, "Reserved, must be 0"),
    ("size_of_image", 4, "Size of bytes in image as loaded in memory, must be multiple of section_alignment"),
    ("size_of_headers", 4, "Combined size of DOS Stub, PE header, and Section headers, rounded to multiple of file_alignment"),
    ("checksum", 4, "Image file checksum as computed by imaghelp.dll"),
    ("subsystem", 2, "Subsystem required to run, see subsytem_description"),
    ("dll_characteristics", 2, "DLL characteristics - see boolean values"),
    ("size_of_stack_reserve", 8, "Memory reserved for stack"),
    ("size_of_stack_commit", 8, "Memory initially commited for the stack, additional pages added as needed"),
    ("size_of_heap_reserve", 8, "Memory reserved for local heap"),
    ("size_of_heap_commit", 8, "Memory initially commited for the local heap, additional pages added as needed"),
    ("loader_flags", 4, "Reserved - must be 0"),
    ("number_of_data_directories", 4, "Number of data directory entries following"),
  ]
image_optional_header_pe32_plus_str = "=QLLHHHHHHLLLLHHQQQQLL"

subsystem_enum = { 
    0:"Unknown",
    1:"Native",
    2:"Windows GUI",
    3:"Windows CUI",
    7:"POSIX CUI",
    9:"Windows CE GUI",
    10:"EFI Application",
    11:"EFI Boot Service Driver",
    12:"EFI Runtime Driver",
    13:"EFI ROM Image",
    14:"XBOX",
  }

dll_characteristics_mask = [
    ("DYNAMIC_BASE", 0x0040, "DLL can be relocated at load time"),
    ("FORCE_INTEGRITY", 0x0080, "Code integrity checks enforced"),
    ("NX_COMPAT", 0x0100, "Image is NX compatible"),
    ("NO_ISOLATION", 0x0200, "Isolation aware, but do not isolate"),
    ("NO_SEH", 0x0400, "Does not use structured exxception handling"),
    ("NO_BIND", 0x0800, "Do not bind"),
    ("WDM_DRIVER", 0x2000, "A WDM driver"),
    ("TERMINAL_SERVER_AWARE", 0x8000, "DLL is terminal server aware"),
  ]
  
data_directory_spec = [
    ("export_table", 8, "The export table address and size"),
    ("import_table", 8, "The import table address and size"),
    ("resource_table", 8, "The resource table address and size"),
    ("exception_table", 8, "The exception table address and size"),
    ("certificate_table", 8, "The certificate table address and size"),
    ("base_relocation_table", 8, "The base relocation table address and size"),
    ("debug", 8, "The debug data address and size"),
    ("architecture", 8, "Reserved must be 0"),
    ("global_ptr", 8, "The RVA of the value to be stored in the global pointer register, size must be 0"),
    ("tls_table", 8, "The thread local storage table address and size"),
    ("load_config_table", 8, "The load configuration table address and size"),
    ("bound_import_table", 8, "The bound import table address and size"),
    ("IAT", 8, "The import address table address and size"),
    ("delay_import_table", 8, "The delay import descriptor address and size"),
    ("clr_runtime_header", 8, "The common language runtime header address and size"),
    ("reserved", 8, "Must be 0"),
  ]
data_directory_str = "=LL" # (address, length)
  
section_header_spec = [
    # Size, Field, Description
    ("name", 8, "Name of the section"),
    ("virtual_size", 4, "Total size of the section loaded into memory, 0 for ojbect files"),
    ("virtual_address", 4, "Address of the first byte of the section relative to image base in memory"),
    ("size_of_raw_data", 4, "Size of the initialized data on disc, must be a multiple of file_alignment"),
    ("pointer_to_raw_data", 4, "File pointer to the first page of the section of the COFF file"),
    ("pointer_to_relocations", 4, "File pointer to the begining of the relocations for the sections, 0 for executables"),
    ("pointer_to_line_numbers", 4, "File pointer to the begining of the line numbers for the section, 0 for executables"),
    ("number_of_relocations", 2, "Number of relocation entries for the section, 0 for executables"),
    ("number_of_line_numbers", 2, "Number of line numbers for the section, 0 for executables"),
    ("characteristics", 4, "Characteristics of the section"),
  ]
section_header_str = "=8sLLLLLLHHL"
  
section_characteristics_mask = [
    ("TYPE_NO_PAD",            0x00000008, "Section should not be padded to the next boundry, replaced by ALIGN_1BYTES"),
    ("CNT_CODE",               0x00000020, "Executable code"),
    ("CNT_INITIALIZED_DATA",   0x00000040, "Initialized data"),
    ("CNT_UNINITIALIZED_DATA", 0x00000080, "Uninitialized data"),
    ("LNK_OTHER",              0x00000100, "Reserved"),
    ("LNK_INFO",               0x00000200, "Comments, valid for object files only"),
    ("LNK_REMOVE",             0x00000800, "Not part of image, valid for object files only"),
    ("LNK_COMDAT",             0x00001000, "Contains COMDAT data, valid for object files only"),
    ("GPREL",                  0x00008000, "Contains data referenced through global pointer (GP)"),
    ("MEM_PURGEABLE",          0x00020000, "Reserved"),
    ("MEM_LOCKED",             0x00040000, "Reserved"),
    ("MEM_PRELOAD",            0x00080000, "Reserved"),
    ("ALIGN_1BYTES",           0x00100000, "Align data on 1 byte boundary, valid for object files only"),
    ("ALIGN_2BYTES",           0x00200000, "Align data on 2 byte boundary, valid for object files only"),
    ("ALIGN_4BYTES",           0x00300000, "Align data on 4 byte boundary, valid for object files only"),
    ("ALIGN_8BYTES",           0x00400000, "Align data on 8 byte boundary, valid for object files only"),
    ("ALIGN_16BYTES",          0x00500000, "Align data on 16 byte boundary, valid for object files only"),
    ("ALIGN_32BYTES",          0x00600000, "Align data on 32 byte boundary, valid for object files only"),
    ("ALIGN_64BYTES",          0x00700000, "Align data on 64 byte boundary, valid for object files only"),
    ("ALIGN_128BYTES",         0x00800000, "Align data on 128 byte boundary, valid for object files only"),
    ("ALIGN_256BYTES",         0x00900000, "Align data on 256 byte boundary, valid for object files only"),
    ("ALIGN_512BYTES",         0x00A00000, "Align data on 512 byte boundary, valid for object files only"),
    ("ALIGN_1024BYTES",        0x00B00000, "Align data on 1024 byte boundary, valid for object files only"),
    ("ALIGN_2048BYTES",        0x00C00000, "Align data on 2048 byte boundary, valid for object files only"),
    ("ALIGN_4096BYTES",        0x00D00000, "Align data on 4096 byte boundary, valid for object files only"),
    ("ALIGN_8192BYTES",        0x00E00000, "Align data on 8192 byte boundary, valid for object files only"),
    ("NRELOC_OVFL",            0x01000000, "Section contains extended relocations"),
    ("MEM_DISCARDABLE",        0x02000000, "Section can be discarded"),
    ("MEM_NOT_CACHED",         0x04000000, "Section cannot be cached"),
    ("MEM_NOT_PAGED",          0x08000000, "Section is not pageable"),
    ("MEM_SHARED",             0x10000000, "Section can be shared in memory"),
    ("MEM_EXECUTE",            0x20000000, "Section can be executed as code"),
    ("MEM_READ",               0x40000000, "Section can be read"),
    ("MEM_WRITE",              0x80000000, "Section can be written to"),
  ]

# (name, offset, desc)
image_coff_header_spec = [
    ("machine", 2, "Type of target machine"),
    ("number_of_sections", 2, "Number of sections"),
    ("time_date_stamp", 4, "Time the file was created"),
    ("pointer_to_symbol_table", 4, "File offset to coff symbol table - should be zero"),
    ("number_of_symbols", 4, "Number of symbols in the coff symbol table - should be zero"),
    ("size_of_optional_header", 2, "Should be zero for object files, valid for executables"),
    ("characteristics", 2, "Attributes of the file - see boolean values"),
  ]
image_coff_header_str = "=HHLLLHH"

image_coff_characteristic_mask = [
    ("RELOCS_STRIPPED", 0x0001, "File must be loaded at preferred base address"),
    ("EXECUTABLE_IMAGE", 0x0002, "Image file can be executed"),
    ("LINE_NUMS_STRIPPED", 0x0004, "Deprecated - should be zero"),
    ("LOCAL_SYMS_STRIPPED", 0x0008, "Deprecated - should be zero"),
    ("AGGRESSIVE_WS_TRIM", 0x0010, "Aggressively trim working set - obsolete for win>2000"),
    ("LARGE_ADDRESS_AWARE", 0x0020, "Address can handle > 2G addressess"),
    ("BYTES_REVERSED_LO", 0x0080, "Deprecated - should be zero"),
    ("32_BIT_MACHINE", 0x0100, "Machine is 32 bit"),
    ("DEBUG_STRIPPED", 0x0200, "Debugging information has been removed"),
    ("REMOVABLE_RUN_FROM_SWAP", 0x0400, "If on removable media, fully load and copy to swap file"),
    ("NET_RUN_FROM_SWAP", 0x0800, "If on newwork media, fully load and copy to swap file"),
    ("SYSTEM", 0x1000, "File is a system file not a user program"),
    ("DLL", 0x2000, "File is a dll"),
    ("UP_SYSTEM_ONLY", 0x4000, "Should only be run on a uniprocessor system only"),
    ("BYTES_REVERSED_HI", 0x8000, "Deprecated - should be zero"),
  ]

machine_enum = {
    0x0     : "Unknown",
    0x1d3   : "Matsushita AM33",
    0x864   : "AMD64",
    0x1c0   : "ARM little endian",
    0x1c4   : "ARMv7 Thumb mode",
    0xebc   : "EFI bytecode",
    0x14c   : "Intel 386",
    0x200   : "Intel Itanium",
    0x9041  : "Mitsubishi M32R little endian",
    0x266   : "MIPS16",
    0x366   : "MIPS with FPU",
    0x466   : "MIPS16 with FPU",
    0x1f0   : "PowerPC little endian",
    0x1f1   : "PowerPC with floating point support",
    0x166   : "MIPS little endian",
    0x1a2   : "Hitachi SH3",
    0x1a3   : "Hitachi SH3 DSP",
    0x1a6   : "Hitachi SH4",
    0x1a8   : "Hitachi SH5",
    0x1c2   : "ARM or Thumb",
    0x169   : "MIPS little endian WCE v2",
  }
    
def parse_section_header_table(coff_header, pe_base, data, offsets):
    vals = {}
    section_table_base = coff_header["size_of_optional_header"] + pe_base + struct.calcsize(image_coff_header_str)
    number_of_sections = coff_header["number_of_sections"]
    section_header_len = struct.calcsize(section_header_str)
    if section_table_base == None or number_of_sections == None:
        return None, offsets
    if section_table_base + number_of_sections * section_header_len > len(data):
        logger.warn("Invalid number of sections")
        return None, offsets
        
    current_offset = section_table_base
    for i in xrange(number_of_sections):
        section, offsets = parse_section_header(current_offset, data, offsets)
        vals[section["name"]] = section
        #offsets[current_offset] = [{"len":section_header_len, "string":"Section Definition: " + section["name"]}]
        current_offset += section_header_len
    return vals, offsets
    

def parse_section_header(section_header_base, data, offsets):
    vals = {}
    section_header_len = struct.calcsize(section_header_str)
    if section_header_base + section_header_len > len(data):
        return None, offsets
    val_data = struct.unpack(section_header_str, data[section_header_base:section_header_base+section_header_len])
    
    for offset, elem in enumerate(section_header_spec):
        vals[elem[0]] = val_data[offset]
        
    characteristics = vals["characteristics"]
    vals["characteristics"] = {}
    for elem in section_characteristics_mask:
        vals["characteristics"][elem[0]] = bool(characteristics & elem[1])
    offsets = build_section_offsets(section_header_base, vals, offsets)
    return vals, offsets     
                              
def parse_data_directory(dd_offset, sections, optional_header, data, offsets):
    vals = {}
    num = optional_header["number_of_data_directories"]
    entry_len = struct.calcsize(data_directory_str)
    if dd_offset + entry_len * num > len(data):
        return None, offsets
    if num > 16:
        num = 16
    current = dd_offset
    for index, elem in enumerate(data_directory_spec):
        if index > num:
            break
        addr, length = struct.unpack(data_directory_str, data[current:current+entry_len])
        offset = addr
        if not offset: offset = 0
        entry = {"virtual_address": addr, "length": length, "offset": offset, "name": elem[0]}
        vals[elem[0]] = entry
        offsets[current] = {"len":entry_len, "string":"Data Directory Entry: %s at %s (RVA), length %s"%(elem[0], addr, length)}
        current += entry_len
        
    return vals, offsets
    
    
def parse_optional_header_fixed(pe_base, data, offsets):
    vals = {}
    coff_len = struct.calcsize(image_coff_header_str)
    base_offset = pe_base + coff_len
    base_len = struct.calcsize(image_optional_header_base_str)
    pe32_len = struct.calcsize(image_optional_header_pe32_str)
    opt_len = base_len + pe32_len
    opt_end = base_offset + opt_len
    if len(data) < opt_end:
        if len(data) < 4096:       # if PE is less than one page, it will be allocated a page 
            data += "\x00"*4096    # which is padded with 0x0s.  (see TinyPE)
        else:
            return None, None, offsets
    val_data = struct.unpack(image_optional_header_base_str, data[base_offset:base_offset+base_len])
    for offset, elem in enumerate(image_optional_header_base_spec):
        vals[elem[0]] = val_data[offset]
    pe32_offset = base_offset + base_len
    if vals["magic_type"] == 0x20B:  # Use 64-bit pe+ header structure (do additional length checking)
        pe32_plus_len = struct.calcsize(image_optional_header_pe32_plus_str)
        opt_len = base_len + pe32_plus_len
        opt_end = base_offset + opt_len
        if len(data) < opt_end:
            return None, None, offsets
        val_data = struct.unpack(image_optional_header_pe32_plus_str, data[pe32_offset:pe32_offset+pe32_plus_len])
        for offset, elem in enumerate(image_optional_header_pe32_plus_spec):
            vals[elem[0]] = val_data[offset]
    else: # Use 32-bi pe header structure
        val_data = struct.unpack(image_optional_header_pe32_str, data[pe32_offset:pe32_offset+pe32_len])
        for offset, elem in enumerate(image_optional_header_pe32_spec):
            vals[elem[0]] = val_data[offset]
    characteristics = vals["dll_characteristics"]
    vals["dll_characteristics"] = {}
    for elem in dll_characteristics_mask:
        vals["dll_characteristics"][elem[0]] = bool(characteristics & elem[1])
    try:
        vals["subsystem_description"] = subsystem_enum[vals["subsystem"]]
    except KeyError:
        vals["subsystem_description"] = "Not valid"
    
    offsets = build_offset_strings(vals, base_offset, offsets)
    return vals, opt_end, offsets
    
def build_section_offsets(base, section, offsets):
    offset = base
    for elem in section_header_spec:
        len = elem[1]
        s = "%s: %s  (%s)"%(elem[0], str(section[elem[0]]).strip('\x00'), elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    return offsets
        
def build_offset_strings(opt_header, base, offsets):
    offset = base
    for elem in image_optional_header_base_spec:
        len = elem[1]
        if len > 4:
            s = "%s (%s)"%(elem[0], elem[2])
        else:
            s = "%s: %s  (%s)"%(elem[0], opt_header[elem[0]], elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    if opt_header["magic_type"] == 0x20B:  # pe+
        for elem in image_optional_header_pe32_plus_spec:
            len = elem[1]
            if len > 4:
                s = "%s (%s)"%(elem[0], elem[2])
            else:
                s = "%s: %s  (%s)"%(elem[0], opt_header[elem[0]], elem[2])
            offsets[offset].append({"len":len, "string":s})
            offset += len
    else:  # 32-bit pe
        for elem in image_optional_header_pe32_spec:
            len = elem[1]
            if len > 4:
                s = "%s (%s)"%(elem[0], elem[2])
            else:
                s = "%s: %s  (%s)"%(elem[0], opt_header[elem[0]], elem[2])
            offsets[offset].append({"len":len, "string":s})
            offset += len
    return offsets
