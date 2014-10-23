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

logger = logging.getLogger("parse_pe")
image_dos_header_spec = None

def parse_pe(data, file_id):
    header = {}
    header["dos_header"] = None
    header["dos_stub"] = None
    header["coff_header"] = None
    header["optional_header"] = None
    header["offsets"] = None
    offsets = {}
    global oid 
    oid = file_id
    dos_header = parse_dos_header(data)    
    if not dos_header:
        logger.warn("DOS Header not found in %s"%oid)
        return None
    header["dos_header"] = dos_header
    header["dos_stub"], ds_start, ds_end = parse_dos_stub(dos_header, data)
    offsets["dos_header"] = (0, ds_start)
    offsets["dos_stub"] = (ds_start, ds_end)
    
    pe_sig_offset = dos_header["lfanew"]
    offsets["pe_signature"] = (pe_sig_offset, pe_sig_offset+4)
    pe_signature = parse_pe_signature(pe_sig_offset, data)
    if not pe_signature:
        logger.warn("PE signature not found in %s"%oid)
        return header
    header["pe_signature"] = pe_signature
    
    pe_base = pe_sig_offset + len(pe_signature)
    coff_header = parse_coff_header(pe_base, data)
    if not coff_header:
        return header
    if coff_header["size_of_optional_header"] == 0 or pe_signature.endswith("PE"): 
        logger.warn("Optional header not found in %s"%oid)
        return header
    header["coff_header"] = coff_header
            
    number_of_sections = coff_header["number_of_sections"]
    optional_header, data_directory_offset = parse_optional_header_fixed(pe_base, data)
    header["optional_header"] = optional_header
    if not header["optional_header"]:
        logger.warn("Optional header not found in %s"%oid)
        return header
    if not data_directory_offset:
        logger.warn("Section table not found in %s"%oid)
        return header
        
    section_table_offset = coff_header["size_of_optional_header"] + pe_base + struct.calcsize(image_coff_header_str)
    section_table = parse_section_header_table(coff_header, section_table_offset, data)
    if section_table:
        for s in section_table:
            if section_table[s]["pointer_to_raw_data"] % optional_header["file_alignment"]:
                logger.warn("Misaligned section in %s"%oid)
    
    header["section_table"] = section_table
        
    dd = parse_data_directory(data_directory_offset, section_table, optional_header, data)
    header["data_directories"] = dd
    
    certificate_table = parse_certificate_table(dd, data)
    header["certificate_table"] = certificate_table
    
    import_table = parse_import_table(dd, section_table, optional_header, data)
    header["import_table"] = import_table
    
    delay_import_table = parse_delay_import_table(dd, section_table, optional_header, data)
    header["delay_import_table"] = delay_import_table
    
    relocs = parse_base_relocations(dd, section_table, data)
    header["relocations"] = relocs
    
    exports = parse_exports_directory_table(dd, section_table, optional_header, data)
    header["exports_directory_table"] = exports
    
    header["resources"] = parse_resource_directory(dd, section_table, optional_header, data)
    
    header["offsets"] = offsets
    return header


# (name, offset, desc)
image_dos_header_spec = [ ("magic", 2, "magic number"),
    ("cblp", 2, "Bytes on last page of file"),
    ("cp", 2, "Pages in file"),
    ("crlc", 2, "Relocations"),
    ("cparhdr", 2, "Size of header in paragraphs"),
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
  
certificate_table_spec = [
    ("length", 4, "Length of the certificate"),
    ("revision", 2, "Certificate version number"),
    ("type", 2, "Type of the content"),
  ]
certificate_table_str = "=LHH"

delay_import_table_spec = [
    ("attributes", 4, "Must be 0"),
    ("name_rva", 4, "RVA of the name of the DLL to be loaded"),
    ("module_handle", 4, "RVA of the module handle to be loaded"),
    ("delay_import_address_table", 4, "RVA of the delay load import address table"),
    ("delay_import_name_table", 4, "RVA of the delay import name table"),
    ("bound_delay_import_table", 4, "RVA of the bound delay load address table, if it exists"),
    ("unload_delay_import_table", 4, "RVA of the bound delay unload address table, should be an exact copy of the delay IAT"),
    ("timestamp", 4, "Timestamp of the DLL to which the image has been bound"),
  ]
delay_import_table_str = "=LLLLLLLL"

import_table_spec = [
    ("import_lookup_table", 4, "RVA of import lookup table, containing name or ordinal for each import"),
    ("time_date_stamp", 4, "Time and date, 0 until bound then set to values for the DLL"),
    ("forwarder_chain", 4, "Index of first forwarder reference"),
    ("name_rva", 4, "RVA of the ASCII string containing the name of the DLL"),
    ("import_address_table", 4, "RVA of import address table, identical to import_lookup_table until image is bound"),
  ]
import_table_str = "=LLLLL"

import_lookup_table_32_spec = [
    ("name_or_ordinal", 4, "If first bit is set, ordinal number, otherwise RVA to name"),
  ]
import_lookup_table_32_str = "=L"

import_lookup_table_64_spec = [
    ("name_or_ordinal", 8, "If first bit is set, ordinal number, otherwise RVA to name"),
  ]
import_lookup_table_64_str = "=Q"

base_relocation_block_spec = [
    ("page_rva", 4, "Image base + page RVA + offset = address of base relocation"),
    ("block_size", 4, "Total number of bytes in the base relocation block"),
  ]  
base_relocation_block_str = "=LL"

base_relocation_spec = [
    ("type_offset", 2, "First 4 bits is the type followed by 12 bits of offset"),
  ]
base_relocation_str = "=H"  

base_relocation_type_enum = {
    0:"absolute",
    1:"high16",
    2:"low16",
    3:"high_low", # Adjust full 32 bits
    4:"high_adj", # Takes 2 slots
    5:"mips_jmpaddr_arm_mov32a", 
    7:"arm_mov32t",
    9:"mips_jumpaddr16",
    10:"dir64",
}

exports_directory_table_spec = [
    ("export_flags", 4, "Reserved must be 0"),
    ("time_date_stamp", 4, "Time date the export was created"),
    ("major_version", 2, "Major version number"),
    ("minor_version", 2, "Minor version number"),
    ("name_rva", 4, "RVA of the name of the DLL"),
    ("ordinal_base", 4, "Starting ordinal number usually set to 1"),
    ("address_table_entries", 4, "Number of entries in the address table"),
    ("number_of_name_pointers", 4, "Number of entries in the name pointer table"),
    ("export_address_table_rva", 4, "Address of the export address table"),
    ("name_pointer_rva", 4, "Address of the export name pointer table"),
    ("ordinal_table_rva", 4, "Address of the ordinal table"),
  ]
exports_directory_table_str = "=LLHHLLLLLLL"

exports_address_table_spec = [
    ("address", 4, "Address of the exported function or name of forwarded DLL"),
  ]
exports_address_table_str = "=L"

exports_name_pointer_table_spec = [
    ("name_pointer", 4, "Address of the name"),
  ]
exports_name_pointer_table_str = "=L"

exports_ordinal_table_spec = [
    ("ordinal", 2, "Ordinal value for the address of the export"),
  ]
exports_ordinal_table_str = "=H"


resource_directory_table_spec = [
    ("characteristics", 4, "Reserved should be set to 0"),
    ("time_date_stamp", 4, "Time date the resource was created"),
    ("major_version", 2, "Major version number"),
    ("minor_version", 2, "Minor version number"),
    ("number_of_name_entries", 2, "The number of name entries"),
    ("number_of_id_entries", 2, "The number of id entries"),
  ]
resource_directory_table_str = "=LLHHHH"

resource_directory_entries_spec = [
    ("name_integer", 4, "Address or integer of the type, name or language id depending on the table"),
    ("data_entry_subdirectory", 4, "High bit 0: offset to resource data entry, High bit 1: offset to resource directory table"),
  ]
resource_directory_entries_str = "=LL"

resource_string_spec = [
    ("length", 2, "Size of the string"),
  ]
resource_string_str = "=H"

resource_data_entry_spec = [
    ("rva", 4, "Address of the resource data"),
    ("size", 4, "The size in bytes of the resource data"),
    ("codepage", 4, "The code page that is used to decode the resource data"),
    ("reserved", 4, "Reserved should be zero"),
  ]
resource_data_entry_str = "=LLLL"

def parse_resource_directory(dd, sections, optional_header, data):
    if not dd or "resource_table" not in dd:
        return None
    base, table_len = dd["resource_table"]["offset"], dd["resource_table"]["length"]
    if base == 0 and table_len == 0:
        return None
    base = rva_to_offset(base, sections)
    if not base:
        return None
    resource_table = {}
    resource_type_table = parse_resource_directory_table(base, base, sections, optional_header, data)
    resource_table["resource_type_table"] = resource_type_table
    resource_name_entries = []
    if resource_type_table and resource_type_table["name_entries"]:
        resource_name_entries.extend(resource_type_table["name_entries"])
    if resource_type_table and resource_type_table["id_entries"]:
        resource_name_entries.extend(resource_type_table["id_entries"])
    resource_name_tables = []
    for entry in resource_name_entries:
        offset = entry["data_entry_subdirectory"]
        entry["resource_name_tables"] = []
        if entry["type"] == "subdirectory":
            name_table = parse_resource_directory_table(base+offset, base, sections, optional_header, data)
            resource_language_entries = []
            if name_table and name_table["name_entries"]:
                resource_language_entries.extend(name_table["name_entries"])
            if name_table and name_table["id_entries"]:
                resource_language_entries.extend(name_table["id_entries"])
            language_tables = []
            for l_entry in resource_language_entries:
                offset = l_entry["data_entry_subdirectory"]
                if l_entry["type"] == "subdirectory":
                    language_entry = parse_resource_directory_table(base+offset, base, sections, optional_header, data)
                    language_tables.append( language_entry )
            if name_table:
                name_table["resource_language_tables"] = language_tables
                entry["resource_name_tables"].append( name_table )
            
    return resource_table


def parse_data_entry(base, data):
    header_len = struct.calcsize(resource_data_entry_str)
    vals = {}
    if base + header_len >= len(data):
        return None
    val_data = struct.unpack(resource_data_entry_str, data[base:base+header_len])
    for n, elem in enumerate(resource_data_entry_spec):
        vals[elem[0]] = val_data[n]
    return vals


def parse_resource_directory_table(base, section_base, sections, optional_header, data):
    header_len = struct.calcsize(resource_directory_table_str)
    if base + header_len >= len(data):
        return None
    val_data = struct.unpack(resource_directory_table_str, data[base:base+header_len])
    vals = {}
    for n, elem in enumerate(resource_directory_table_spec):
        vals[elem[0]] = val_data[n]
        
    num_name_entries = vals["number_of_name_entries"]
    num_id_entries = vals["number_of_id_entries"]
    base += header_len
    entry_len = struct.calcsize(resource_directory_entries_str)
    if entry_len * (num_name_entries+num_id_entries) + base > len(data):
        logger.warning("Resource table walked off the end of data in %s"%oid)
        return None
        
    vals["name_entries"] = parse_resource_directory_entry(num_name_entries, base, section_base, data)
    spec_len = struct.calcsize(resource_string_str)
    
    offset_set = set()
    for entry in vals["name_entries"]:
        offset = section_base + entry["name_integer"] & 0b01111111111111111111111111111111
        if offset in offset_set:
            break
        offset_set.add(offset)
        if offset + spec_len > len(data):
            break
        str_len = struct.unpack(resource_string_str, data[offset:offset+spec_len])[0]
        try:
            uni_str = unicode(data[offset+spec_len:offset+spec_len+str_len])
        except UnicodeDecodeError:
            uni_str = unicode("***Invalid Unicode***")
        entry["name"] = uni_str
    
    base += entry_len * num_name_entries
    vals["id_entries"] = parse_resource_directory_entry(num_id_entries, base, section_base, data)
    return vals
    

def parse_resource_directory_entry(num_entries, base, section_base, data):
    entry_len = struct.calcsize(resource_directory_entries_str)
    entries = []
    offset = base
    for i in xrange(num_entries):
        if offset + entry_len >= len(data):
            break
        val_data = struct.unpack(resource_directory_entries_str, data[offset:offset+entry_len])
        entry = {}
        for n, elem in enumerate(resource_directory_entries_spec):
            entry[elem[0]] = val_data[n]
        type = (entry["data_entry_subdirectory"] & 0b10000000000000000000000000000000) >> 31
        value = entry["data_entry_subdirectory"] & 0b01111111111111111111111111111111 
        entry["data_entry_subdirectory"] = value
        if type:
            entry["type"] = "subdirectory"
        else:
            entry["type"] = "data"
            data_rva = entry["data_entry_subdirectory"]+section_base
            entry["data"] = parse_data_entry(data_rva, data)
        entries.append(entry)
        offset += entry_len
    return entries


def parse_exports_directory_table(dd, sections, optional_header, data):
    if not dd or "export_table" not in dd:
        return None
    base, table_len = dd["export_table"]["offset"], dd["export_table"]["length"]
    if base == 0 and table_len == 0:
        return None
    str_len = struct.calcsize(exports_directory_table_str)
    base = rva_to_offset(base, sections)
    if not base or base + str_len >= len(data):
        return None
    val_data = struct.unpack(exports_directory_table_str, data[base:base+str_len])
    vals = {}
    for n, elem in enumerate(exports_directory_table_spec):
        vals[elem[0]] = val_data[n]
        
    base = vals["export_address_table_rva"]
    base = rva_to_offset(base, sections)    
    entry_len = struct.calcsize(exports_address_table_str)
    addresses = []
    for i in xrange(vals["address_table_entries"]):
        if not base or base + entry_len >= len(data):
            break
        address = struct.unpack(exports_address_table_str, data[base:base+entry_len])
        addresses.append(address)
        base += entry_len
    
    base = vals["name_pointer_rva"]
    base = rva_to_offset(base, sections)
    if not base:
        return None
    entry_len = struct.calcsize(exports_name_pointer_table_str)
    export_names = []
    for i in xrange(vals["number_of_name_pointers"]):
        if base + entry_len >= len(data):
            break
        name_ptr = struct.unpack(exports_name_pointer_table_str, data[base:base+entry_len])
        name = rva_string_lookup(name_ptr[0], sections, optional_header["image_base"], data)
        base += entry_len
        if name:
            export_names.append(name)
    
    base = vals["ordinal_table_rva"]
    base = rva_to_offset(base, sections)    
    entry_len = struct.calcsize(exports_ordinal_table_str)
    ords = []
    for i in xrange(vals["number_of_name_pointers"]):
        if not base or base + entry_len >= len(data):
            break
        ord = struct.unpack(exports_ordinal_table_str, data[base:base+entry_len])
        ords.append(ord)
        base += entry_len
            
    exports = {}
    for n, o in zip(export_names, ords):
        if o < len(addresses):
            exports[n] = addresses[o]
            
    vals["export_names"] = exports
    return vals


def parse_base_relocations(dd, sections, data):
    if not dd or "base_relocation_table" not in dd:
        return None
    base, table_len = dd["base_relocation_table"]["offset"], dd["base_relocation_table"]["length"]
    if base == 0 and table_len == 0:
        return None
    entry_len = struct.calcsize(base_relocation_block_str)
    base = rva_to_offset(base, sections)
    if not base:
        return None
    offset = base
    relocations = []
    while offset - base < table_len and offset+entry_len < len(data):
        val_data = struct.unpack(base_relocation_block_str, data[offset:offset+entry_len])
        block = {}
        for n, elem in enumerate(base_relocation_block_spec):
            block[elem[0]] = val_data[n]
        rels = []
        s = block["block_size"]
        offset += entry_len
        s -= entry_len
        num_entries = s / struct.calcsize(base_relocation_str)
        rlen = struct.calcsize(base_relocation_str)
        for i in xrange(num_entries):
            if offset + rlen >= len(data):
                break
            type_offset = struct.unpack(base_relocation_str, data[offset:offset+rlen])
            type_val = (type_offset[0] & 0b1111000000000000) >> 12
            offset_val = type_offset[0] & 0b0000111111111111
            rels.append((type_val, offset_val))
            offset += rlen
        block["relocations"] = rels
            
        relocations.append(block)
    
    return relocations
        

def rva_to_offset(rva, sections, image_base=0):
    if not sections:
        return None
    for s in sections:
        v_add = sections[s]["virtual_address"]
        v_size = sections[s]["virtual_size"]
        if rva >= v_add and rva < v_add + v_size:
            f_add = sections[s]["pointer_to_raw_data"] + rva - v_add
            return f_add
    if image_base and rva > image_base:
        return rva_to_offset(rva-image_base, sections, image_base=0)
    return None
    
     
def rva_string_lookup(rva, sections, image_base, data):
    if not rva:
        return None
    f_offset = rva_to_offset(rva, sections, image_base)
    if not f_offset:   
        return None
    string_end = data[f_offset:].find("\x00")
    return data[f_offset:f_offset+string_end]
    
    
def parse_import_lookup_table(base, base_rva, optional_header, sections, data):
    if not base:
        return None
    pe_type = optional_header["magic_type"]
    if pe_type == 0x20b:
        spec = import_lookup_table_64_spec
        s = import_lookup_table_64_str
    else:
        spec = import_lookup_table_32_spec
        s = import_lookup_table_32_str
    
    entry_len = struct.calcsize(s)
    vals = []
    offset = base
    while offset + entry_len < len(data):
        val_data = struct.unpack(s, data[offset:offset+entry_len])
        if val_data[0] == 0:
            break
        if ( (pe_type == 0x20b and val_data[0] & 0x8000000000000000) or
             (pe_type != 0x20b and val_data[0] & 0x80000000) ):
            ordinal = val_data[0] & 0xff
            vals.append(ordinal)    
        else:
            name_rva = val_data[0]
            name = rva_string_lookup(name_rva+2, sections, optional_header["image_base"], data)
            if not name:  
                break
            vals.append(name)
        offset += entry_len
                
    return vals

def parse_import_address_table(base, base_rva, optional_header, sections, data):
    if not base:
        return None
    pe_type = optional_header["magic_type"]
    if pe_type == 0x20b:
        spec = import_lookup_table_64_spec
        s = import_lookup_table_64_str
    else:
        spec = import_lookup_table_32_spec
        s = import_lookup_table_32_str
    
    entry_len = struct.calcsize(s)
    vals = {}
    offset = base
    rva = base_rva
    while offset + entry_len < len(data):
        val_data = struct.unpack(s, data[offset:offset+entry_len])
        if not val_data[0]:
            break
        if ( (pe_type == 0x20b and val_data[0] & 0x8000000000000000) or
             (pe_type != 0x20b and val_data[0] & 0x80000000) ):
            ordinal = val_data[0] & 0xff
            vals[rva + optional_header["image_base"]] = ordinal    
        else:
            name_rva = val_data[0]
            name = rva_string_lookup(name_rva+2, sections, optional_header["image_base"], data)
            if not name:  
                break
            vals[rva + optional_header["image_base"]] = name
        offset += entry_len
        rva += entry_len
                
    return vals

def parse_import_table(dd, sections, optional_header, data):
    if not dd or "import_table" not in dd:
        return None
    base_rva, table_len = dd["import_table"]["offset"], dd["import_table"]["length"]
    if base_rva == 0 and table_len == 0:
        return None
    base = rva_to_offset(base_rva, sections)
    if not base:
        return None
    if base + table_len > len(data):    
        return None
    vals = {}
    entry_len = struct.calcsize(import_table_str)
    current_offset = base
    while current_offset - base < table_len and current_offset + entry_len < len(data):
        val_data = struct.unpack(import_table_str, data[current_offset:current_offset+entry_len])
        check = 0
        for v in val_data:
            if v != 0:
                check = 1
        if not check:
            break
        import_entry = {}
        for offset, elem in enumerate(import_table_spec):
            import_entry[elem[0]] = val_data[offset]
        current_offset += entry_len
        name_rva = import_entry["name_rva"]
        if not name_rva:
            continue
        name = rva_string_lookup(name_rva, sections, optional_header["image_base"], data)
        lookup_table_rva = import_entry["import_lookup_table"]
        lookup_table_offset = rva_to_offset(lookup_table_rva, sections)
        function_names = parse_import_lookup_table(lookup_table_offset, lookup_table_rva, optional_header, sections, data)
        address_table_rva = import_entry["import_address_table"]
        address_table_offset = rva_to_offset(address_table_rva, sections)
        addresses = parse_import_address_table(address_table_offset, address_table_rva, optional_header, sections, data)
        
        import_entry["function_names"] = function_names
        import_entry["addresses"] = addresses
        
        if name:
            vals[name] = import_entry
        else:
            vals[current_offset] = import_entry
        
    return vals
    

def parse_delay_import_table(dd, sections, optional_header, data):
    if not dd or "delay_import_table" not in dd:
        return None
    base, table_len = dd["delay_import_table"]["offset"], dd["delay_import_table"]["length"]
    if not base or not table_len:
        return None
    if base + table_len > len(data):    
        return None
    vals = {}
    entry_len = struct.calcsize(delay_import_table_str)
    base = rva_to_offset(base, sections)
    current_offset = base
    if not base:
        return None
    while current_offset - base < table_len and current_offset + entry_len < len(data):
        val_data = struct.unpack(delay_import_table_str, data[current_offset:current_offset+entry_len])
        check = 0
        for v in val_data:
            if v != 0:
                check = 1
        if not check:
            break
        import_entry = {}
        for offset, elem in enumerate(delay_import_table_spec):
            import_entry[elem[0]] = val_data[offset]
        current_offset +=  entry_len
        name_rva = import_entry["name_rva"]
        if not name_rva:
            continue
        name = rva_string_lookup(name_rva, sections, optional_header["image_base"], data)
        lookup_table_rva = import_entry["delay_import_name_table"]
        lookup_table_offset = rva_to_offset(lookup_table_rva, sections)
        function_names = parse_import_lookup_table(lookup_table_offset, lookup_table_rva, optional_header, sections, data)
        address_table_rva = import_entry["delay_import_address_table"]
        address_table_offset = rva_to_offset(address_table_rva, sections)
        addresses = parse_import_address_table(address_table_offset, address_table_rva, optional_header, sections, data)

        import_entry["function_names"] = function_names        
        import_entry["addresses"] = addresses

        if name:
            vals[name] = import_entry
        else:
            vals[current_offset] = import_entry
        
    return vals

def parse_certificate_table(dd, data):
    if not dd or "certificate_table" not in dd:
        return None
    base, table_len = dd["certificate_table"]["offset"], dd["certificate_table"]["length"]
    if base == 0 and table_len == 0:
        return None
    if base + table_len > len(data):    
        return None
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
        if length % 8 > 0:
            length += 8 - (length % 8)
        current_offset +=  length 
        vals.append(certificate)
    return vals
        
def parse_section_header_table(coff_header, section_table_base, data):
    vals = {}
    number_of_sections = coff_header["number_of_sections"]
    section_header_len = struct.calcsize(section_header_str)
    if section_table_base == None or number_of_sections == None:
        return None
    if section_table_base + number_of_sections * section_header_len > len(data):
        logger.warn("Invalid number of sections in %s"%oid)
        return None
        
    current_offset = section_table_base
    for i in xrange(number_of_sections):
        section = parse_section_header(current_offset, data)
        vals[section["name"]] = section
        current_offset += section_header_len
    return vals
    

def parse_section_header(section_header_base, data):
    vals = {}
    section_header_len = struct.calcsize(section_header_str)
    if section_header_base + section_header_len > len(data):
        return None
    val_data = struct.unpack(section_header_str, data[section_header_base:section_header_base+section_header_len])
    
    for offset, elem in enumerate(section_header_spec):
        vals[elem[0]] = val_data[offset]
        
    characteristics = vals["characteristics"]
    vals["characteristics"] = {}
    for elem in section_characteristics_mask:
        vals["characteristics"][elem[0]] = bool(characteristics & elem[1])
    
    return vals
    
    
def parse_data_directory(dd_offset, sections, optional_header, data):
    vals = {}
    num = optional_header["number_of_data_directories"]
    entry_len = struct.calcsize(data_directory_str)
    if dd_offset + entry_len * num > len(data):
        return None
    if num > 16:
        num = 16
    current = dd_offset
    for offset, elem in enumerate(data_directory_spec):
        if offset > num:
            break
        addr, length = struct.unpack(data_directory_str, data[current:current+entry_len])
        offset = addr
        if not offset: offset = 0
        entry = {"virtual_address": addr, "length": length, "offset": offset, "name": elem[0]}
        vals[elem[0]] = entry
        current += entry_len
        
    return vals
    
    
def parse_optional_header_fixed(pe_base, data):
    vals = {}
    coff_len = struct.calcsize(image_coff_header_str)
    base_offset = pe_base + coff_len
    base_len = struct.calcsize(image_optional_header_base_str)
    pe32_len = struct.calcsize(image_optional_header_pe32_str)
    opt_len = base_len + pe32_len
    opt_end = base_offset + opt_len
    if len(data) < opt_end:
        if len(data) < 4096:       # if PE is less than one page, it will be allocated a page 
            data += "\0x0"*4096    # which is padded with 0x0s.  (see TinyPE)
        else:
            return None, None
    val_data = struct.unpack(image_optional_header_base_str, data[base_offset:base_offset+base_len])
    for offset, elem in enumerate(image_optional_header_base_spec):
        vals[elem[0]] = val_data[offset]
    pe32_offset = base_offset + base_len
    if vals["magic_type"] == 0x20B:  # Use 64-bit pe+ header structure (do additional length checking)
        pe32_plus_len = struct.calcsize(image_optional_header_pe32_plus_str)
        opt_len = base_len + pe32_plus_len
        opt_end = base_offset + opt_len
        if len(data) < opt_end:
            return None, None
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
    
    return vals, opt_end

def parse_coff_header(pe_base, data):
    vals = {}
    spec_len = struct.calcsize(image_coff_header_str)
    if len(data) < pe_base + spec_len:
        return None
    val_data = struct.unpack(image_coff_header_str, data[pe_base:pe_base+spec_len])
    for offset, elem in enumerate(image_coff_header_spec):
        vals[elem[0]] = val_data[offset]
    characteristics = vals["characteristics"]
    vals["characteristics"] = {}
    for elem in image_coff_characteristic_mask:
        vals["characteristics"][elem[0]] = bool(characteristics & elem[1])
    try:
        vals["machine_description"] = machine_enum[vals["machine"]]
    except KeyError:
        vals["subsystem_description"] = "Not Valid"
        
    return vals

def parse_pe_signature(pe_base, data):
    if pe_base >= len(data) - 4:
        return None
    sig = data[pe_base:pe_base+4]
    if sig.startswith("NE") or sig.startswith("LE") or sig.startswith("MZ"):
        sig = sig[:2]
    return sig
                              
def parse_dos_header(data):
    vals = {}
    spec_len = struct.calcsize(image_dos_header_str)
    if len(data) < spec_len:
        return None
    val_data = struct.unpack(image_dos_header_str, data[:spec_len])
    for offset, elem in enumerate(image_dos_header_spec):
        vals[elem[0]] = val_data[offset]
    if vals["magic"] != "MZ":
        return None
    return vals
    
def parse_dos_stub(dos_header, data):
    header_len = struct.calcsize(image_dos_header_str)
    lfanew = dos_header["lfanew"]
    return data[header_len:lfanew], header_len, lfanew
