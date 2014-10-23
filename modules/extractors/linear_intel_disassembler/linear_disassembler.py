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

import histogram
from libdisasm.disasmbuf import DisasmBuffer
from libdisasm.disasm import SingleDisassembler

class MySingleDisassembler(SingleDisassembler):
    """
    Disassembles one instruction and provides access to that instruction.
    Used by LibdisasmDisassembler because of the way the libdisasm interface is
    set up.
    """
    def __init__(self):
        super(MySingleDisassembler, self).__init__()
        self.last_insn = None
    def get_last_insn(self):
        return self.last_insn
    def process(self, buf, insn):
        self.last_insn = insn
        
def disassemble_linear(buf, header, logger):
    sections = header.section_info
    disassembly = dict()
    buf = DisasmBuffer(buf)
    disassembler = MySingleDisassembler()
    entry_sections = []
    for e in header.get_entries():
        entry_sections.append(header.find_section(e))
    for name in sections:
        if sections[name]['section_exec'] == True or sections[name] in entry_sections:
            start_rva    = sections[name]['section_addr']
            length       = sections[name]['section_len']
            start_ph_ofs = sections[name]['section_offset']

            code_sections = header.get_code_chunks_of_section(sections[name])
            for (chunk_ofs, chunk_len) in code_sections:
                chunk_rva = start_rva + chunk_ofs - start_ph_ofs
                chunk_end_ofs = chunk_ofs + chunk_len
                entropy = histogram.calc_entropy(buf[chunk_ofs:chunk_end_ofs])
                if entropy > 0.9:
                    logger.debug("chunk at buf[0x%x:0x%x] appears to be encrypted, skipping.",
                                chunk_ofs, chunk_end_ofs)
                    if sections[name] in entry_sections:    # for encoded sections (UPX), skip to entry point.
                        for e in header.get_entries():
                            if e > chunk_rva and e < chunk_rva + chunk_len:
                                chunk_ofs = header.get_offset(e)
                                chunk_rva = e
                    else:
                        break
                curr_ofs, curr_rva = chunk_ofs, chunk_rva

                logger.debug("disassemble_linear working on buf[0x%x:0x%x]",
                             chunk_ofs, chunk_end_ofs)
                while curr_ofs < chunk_end_ofs and curr_ofs < len(buf):
                    #check if we already have disassembled this instruction
                    disasm = disassembly.get(curr_ofs, None)
                    if not disasm:
                        try:
                            disassembler.disassemble(buf, curr_ofs)
                            libdisasm_insn = disassembler.get_last_insn()
                            disasm = build_insn(curr_rva, curr_ofs, libdisasm_insn)
                        except IndexError, msg:
                            break
                        except Exception, msg:
                            curr_ofs += 1
                            curr_rva += 1
                            logger.debug("Found bad insn: %s", msg)
                            continue
                        disassembly[curr_ofs] = disasm
                    ld = disasm["len"]
                    curr_rva += ld
                    curr_ofs += ld  
                    if buf[curr_ofs:].startswith('\x00'*32):
                        while curr_ofs < len(buf) and buf[curr_ofs] == '\x00':
                            curr_ofs += 1
    return disassembly

def build_insn(addr, offset, libdisasm_insn):
    new_insn = dict()
    new_insn["addr"]  = addr
    new_insn["group"] = libdisasm_insn.group()
    new_insn["mnem"]  = libdisasm_insn.mnemonic()

    raw_ops = libdisasm_insn.operands()
    mylen = len( libdisasm_insn.bytes() )
    new_insn["len"] = mylen

    explicit_ops = [r for r in raw_ops if not r.info()['implicit']]

    # only indicate operands when they are given
    if len(explicit_ops) > 0:
        new_insn["d_op"] = gen_operand(addr, explicit_ops[0], mylen)

    if len(explicit_ops) > 1:
        new_insn["s_ops"] = list()
        for i in range(1,len(explicit_ops)):
            new_insn["s_ops"].append(gen_operand(addr, explicit_ops[i], mylen))

    return new_insn

def gen_operand(addr, libdisasm_op, length):
    gen = {"register"          :init_register,
           "immediate"         :init_immediate,
           "offset"            :init_offset,
           "relative"          :init_relative,
           "relative far"      :init_relative_far,
           "relative near"     :init_relative_near,
           "segment:offset"    :init_segment_offset,
           "effective address" :init_effective_address}[libdisasm_op._info['type']]
    return gen(addr, libdisasm_op, length)

def init_register(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "reg"
    new_op["data"] = libdisasm_op.name()
    return new_op

def init_immediate(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "imm"
    new_op["data"] = libdisasm_op.value().value()
    return new_op

def init_offset(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "off"
    new_op["data"] = libdisasm_op.value().value()
    return new_op

def init_relative(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "rel"
    new_op["data"] = addr + length + libdisasm_op.value().value()
    return new_op

def init_relative_far(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "rel"
    new_op["subtype"] = "far"
    new_op["data"] = addr + length + libdisasm_op.value().value()
    return new_op

def init_relative_near(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "rel"
    new_op["subtype"] = "near"
    new_op["data"] = addr + length + libdisasm_op.value().value()
    return new_op

def init_effective_address(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "eff_addr"
    [ base_reg, index_reg ] = [libdisasm_op.base(), libdisasm_op.index() ]
    [ base_str, index_str ] = [None] * 2
    if base_reg  != None: base_str  =  base_reg.name()
    if index_reg != None: index_str = index_reg.name()
    scale = libdisasm_op.scale()
    if libdisasm_op.disp() != None:
        disp_obj  = libdisasm_op.disp()
        if disp_obj.value() > 4000000000: 
            disp_obj.set_signed(True)
        disp = disp_obj.value()
    else:
        disp = 0
    new_op["data"] = { "base" : base_str,
                       "idx"  : index_str,
                       "scale": scale,
                       "disp" : disp      }
    return new_op

def init_segment_offset(addr, libdisasm_op, length):
    new_op = dict()
    new_op["type"] = "seg_off"
    new_op["data"] = (int(str(libdisasm_op.segment()),16),
                      int(str(libdisasm_op.offset ()),16))
    return new_op
