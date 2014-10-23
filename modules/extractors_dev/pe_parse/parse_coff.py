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

logger = logging.getLogger("parse_coff")

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
                              
def parse_coff_header(pe_base, data, offsets):
    vals = {}
    spec_len = struct.calcsize(image_coff_header_str)
    if len(data) < pe_base + spec_len:
        return None, offsets
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
    
    offsets = build_offset_strings(vals, pe_base, offsets)
    
    return vals, offsets

def parse_pe_signature(pe_base, data, offsets):
    if pe_base >= len(data) - 4:
        return None, offsets
    sig = data[pe_base:pe_base+4]
    if sig.startswith("NE") or sig.startswith("LE") or sig.startswith("MZ"):
        sig = sig[:2]
    offsets[pe_base].append({"len":len(sig), "string": "PE Signature"})
    return sig, offsets

def build_offset_strings(coff_header, base, offsets):
    offset = base
    for elem in image_coff_header_spec:
        len = elem[1]
        if len > 4:
            s = "%s (%s)"%(elem[0], elem[2])
        else:
            s = "%s: %s  (%s)"%(elem[0], coff_header[elem[0]], elem[2])
        offsets[offset].append({"len":len, "string":s})
        offset += len
    return offsets
        
