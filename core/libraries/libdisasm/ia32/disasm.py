#!/usr/bin/env python2.4

'''
    libdisasm.ia32.disasm : IA32 instruction disassembly

    TODO:
        + instruction suffixes
        + instruction signatures
        + implicit operands
        + stack modification
'''

from .. import exception as Excep
from .. import instruction as Insn
from .. import operand as Operand

import isa as IA32
from operand import OperandDecoder
from modrm import ModRM

WC_BYTE = 0xF4

# Disassembler State =====================================================
class DisassemblerState(object):
    ''' 
        Opcode disassembler state
        Keeps track of the many exceptional cases in the 
        Intel x86 decoding "algorithm" 
    '''

    def __init__(self, addr_size):
        # address and operand size: 16-bit or 32-bit
        self.default_addr_size = addr_size
        self.default_op_size = addr_size
        self.reset()

    def reset(self):
        # operand and address size (after override)
        self.addr_size = self.default_addr_size
        self.op_size = self.default_op_size
        # Instruction object
        self.insn = None    # reference to Instruction object
        self.info = None    # info dict for Instruction object
        self.offset = 0        # offset of start of insn
        self.rva = 0        # rva of start of insn
        self.sig = []        # mark wildcard bytes 
        # prefix/suffix support
        self.prefix_groups = [None,None,None,None,None]
        self.num_prefixes = 0
        self.suffix_table = None
        # ModR/M support
        self.has_modrm = False
        self.modrm = None
        # exception support
        self.last_table = ""
        self.last_byte = 0

# Opcode Disassembler ====================================================
class OpcodeDisassembler(object):
    '''
        Intel 32-bit x86 opcode disassembler 

        Usage:
            d = OpcodeDisassembler()
        d.disassemble(buf)
    '''
            

    def __init__(self, addr_size=4):
        ''' Address size can be set to 2 for legacy 16-bit mode '''
        self.state = DisassemblerState(addr_size)
        # instantiate an operand decoder that shares state
        self.operand_decoder = OperandDecoder(self.state)
    
    def max_insn_length(self):
        ''' Max Instruction Length: Officially 17 bytes on intel. '''
        return 17
    
    def signature_wildcard(self):
        return WC_BYTE

    def _exceed_null_limit(self, buf, options):
        ''' Does the buffer exceed the NULL limit?
            Returns true if the buffer starts with > limit NULL bytes
            FIXME: this should really be part of the caller.
        '''
        limit = options.get_option('null_limit')
        if not limit:
            return False
        try:
            for i in buf[0:limit]:
                if i:
                    return False
            return True
        except IndexError:
            return True

    def disassemble(self, buf, options):
        '''
            Returns an Instruction object.
            Throws IndexError when the instruction would 
            extend beyond the bounds of buf.
            Throws DecodeError when an invalid instruction
            is encountered; the buffer can be reset to
            where disassembly started:
                except DecodeError, e:
                    buf.seek(e._start)
        '''
        self.state.reset()

        # store current offset and rva
        self.state.offset = buf.tell()
        self.state.rva = buf.tell_rva()

        if self._exceed_null_limit(buf, options):
            raise RuntimeError # InvalidInstruction

        opcode = self._opcode_lookup(buf, 0)
        insn = self._decode_insn(buf, opcode)
        insn._offset = self.state.offset
        insn._rva = self.state.rva
        return insn
    
    def _prefix(self, op_descr, offset):
        ''' Instruction Prefix
            Add prefix represented by op_descr to list of
            instruction prefixes. Throws a DecodeError if
            more than one prefix from each group is present.
            To get around such cases, advanced the buffer a
            single byte and try again.
        '''
        name = op_descr['info']['prefix_name']
        group = op_descr['info']['prefix_group']
        if self.state.prefix_groups[group]:
            raise Excep.DecodeError(self.state.offset, offset,\
                  self.state.last_table, self.state.last_byte, \
                  "Multiple group " + str(group) + "prefixes.")
        self.state.prefix_groups[group] = name
        self.state.num_prefixes += 1
        
        # handle operand and address size overrides
        if group == 3:
            if self.state.op_size == 2:
                self.state.op_size = 4
            else:
                self.state.op_size = 2

        if group == 4:
            if self.state.addr_size == 2:
                self.state.addr_size = 4
            else:
                self.state.addr_size = 2
                
        return group

    def _uses_modrm(self, op_descr):
        ''' Does the instruction use a ModR/M byte? '''
        modrm_methods = ( 'E', 'M', 'Q', 'R', 'W', 'C', 'D', 'G', 
                          'P','S','T','V' )

        dest = op_descr['dest']
        if dest and dest['addr_method'] in modrm_methods:
            return True

        src = op_descr['src']
        if src and src['addr_method'] in modrm_methods:
            return True

        return False

    def _opcode_byte_lookup(self, buf, table):
        '''
            Opcode byte lookup
            Adjust 'byte' to a proper index value for 'table'
            (needed because of the FPU 'sparse tables')
            and return the opcode description at that index.
            Throws a DecodeError when there are problems.

        '''
        modrm_tables = ('extension', 'fpu')
        descr = IA32.ia32_tables[table]
        byte = int(ord( buf.read() ))

        # if this is one of the segmented (and condensed) FPU tables
        # ...and byte exceeds the table range...
        if descr['type'] == 'fpu' and byte > descr['max']:
            # ...use the next table (always an fpu_ext)
            descr = IA32.ia32_tables[table+1]

        # calculate table index for byte
        byte = (byte >> descr['shift']) & descr['mask']

        if byte > descr['max'] or descr['min'] > byte:
            raise Excep.DecodeError(self.state.offset, buf.tell(),\
                descr['name'], byte, \
                "Byte exceeds opcode table bounds.")
        byte -= descr['min']

        # instruction definition lookup
        op_descr = descr['table'][byte]

        if op_descr['info']['type'] == "invalid":
            raise Excep.DecodeError(self.state.offset, buf.tell(),\
                descr['name'], byte, \
                "Byte defined as invalid instruction in table.")

        # Do not consume a byte for ModR/M opcode extensions
        self.state.has_modrm = self._uses_modrm(op_descr)
        if descr['type'] in modrm_tables and self.state.has_modrm:
            buf.seek(buf.tell()-1)

        # save last_table and last_byte for future exceptions
        self.state.last_table = descr['name']
        self.state.last_byte = byte

        return op_descr

    def _opcode_lookup(self, buf, table):
        '''
           Opcode Lookup:
           Read a byte from 'buf' and look up the corresponding
           opcode description in 'table'. If the opcode is a
           prefix, or part of a multibyte instruction, recurse
           looking up subsequent bytes. 
           Returns the opcode description. Throws an IndexError
           if the end of 'buf' is reached, or 'InvalidInstruction'
           if the bytes in 'buf' do not contain a valid opcode.

           NOTE: This is almost as bad as the C code. Needs fix!
        '''
        # tables which do not always consume a byte during lookup
        extension_tables = ('ext_ext', 'fpu_ext')

        # Lookup opcode in table. This will raise an
        # InvalidInstruction exception if the opcode is not valid.
        op_descr = self._opcode_byte_lookup(buf, table)

        prefix =False
        if op_descr['info']['prefix']:
            # group can be used to roll back the prefix later
            group = self._prefix(op_descr, buf.tell())
            prefix =True

        subtable = op_descr['table']
        

        # The 'table' field contains the id of a table to
        # perform an additional lookup in, using either the
        # current or the next byte. This lookup is handled
        # recursively.
        recurse = False
        if subtable:
            subtable_type = IA32.ia32_tables[subtable]['type']
            # If the subtable type is suffix, then the lookup
            # is performed after operands have been decoded.
            if subtable_type == 'suffix':
                   self.state.suffix_table = subtable
            elif self.state.num_prefixes < 2:
                recurse = True
        else:
            subtable_type = ""

        # A prefix requires recursing on the main table [which
        # is stored in the 'table' field] using the next byte.
        if prefix:
            recurse = True

        if recurse:
            # Some prefixes are either SSE1/2/3 escapes,
            # or actual prefixes. To handle this we
            # attempt to lookup the byte after the prefix 
            # using the SSE table stored in the 'table' field.
            # If this produces an invalid instruction, then
            # the prefix is not an SSE escape and we do the
            # lookup again using the original table.
            # FIXME: there must be a better way...
            if subtable_type in extension_tables:
                buf.seek(buf.tell()-1)
            try:
                # perform lookup using subtable
                op_descr = \
                self._opcode_lookup(buf, subtable)
            except Excep.DecodeError, e:
                if prefix:
                    buf.seek(buf.tell()-1)
                    op_descr = self._opcode_lookup(buf, 
                        table)
                    # Need this to avoid 'fixing' prefix
                    subtable = table
                else:
                    # Not a prefix, not our problem
                    raise e

        # On the off-chance that a prefix byte was actually an
        # escape to an SSE table (i.e. subtable != table), we
        # do not want to add the prefix
        if prefix and subtable != table:
            self.state.prefix_groups[group] = None
            self.state.num_prefixes -= 1

        return op_descr

    def _insn_from_opcode(self, opcode):
        op_list = []

        prefixes = []
        for p in self.state.prefix_groups:
            if p:
                prefixes.append(p)

        self.state.info = opcode['info'].copy()
        self.state.info['address_size'] = self.state.addr_size
        self.state.info['operand_size'] = self.state.op_size
        self.state.info['eflags'] = opcode['eflags'].copy()

        offset = self.state.offset
        rva = self.state.rva

        # 'bytes' is "", 'sig' is "", and 'operands' is []
        # because we do not know those values yet ... but we
        # need an Instruction reference for Relative operands!
        insn = Insn.Instruction(self.state.offset, self.state.rva,
                "", "", opcode['mnemonic'], [], prefixes, 
                self.state.info)

        # store reference for Relative operands
        self.state.insn = insn        

        return insn

    def _decode_insn(self, buf, opcode):
        insn = self._insn_from_opcode(opcode)

        # mark opcode bytes as not wildcards
        self.state.sig = [0] * (buf.tell() - self.state.offset)

        # prefetch modrm byte
        if self.state.has_modrm:
            self.state.modrm = ModRM(buf.peek())

        op = self._explicit_operand( buf, opcode, 'dest' )
        if op:
            insn._operands.append( op )
        op = self._explicit_operand( buf, opcode, 'src' )
        if op:
            insn._operands.append( op )
        op = self._explicit_operand( buf, opcode, 'imm' )
        if op:
            insn._operands.append( op )


        if self.state.suffix_table:
            self._suffix(buf, insn)

        # generate byte string
        insn._bytes = buf[self.state.offset:buf.tell()]
        insn._size = len(insn._bytes)

        # generate byte signature
        # for each byte in bytes:
        # if state.sig is 1, use wildcard, else use original byte.
        insn._signature = ''.join([s[1] and chr(WC_BYTE) or s[0] \
                for s in zip(insn._bytes, self.state.sig) ])

        if opcode['implicit']:
            self._implicit_operands(opcode['implicit'], insn)

        self._stack_mod(insn)

        return insn

    def _suffix(self, buf, insn):
        '''
           Lookup suffix byte and set Instruction object info
           and mnemonic fields accordingly.
        '''
        op_descr = self._opcode_byte_lookup(buf, \
               self.state.suffix_table)

        insn.opcode()._mnemonic = op_descr['mnemonic']
        insn.opcode()._type = op_descr['info']['type']
        insn.opcode()._group = op_descr['info']['group']
        insn.opcode()._cpu = op_descr['info']['cpu']
        insn.opcode()._isa = op_descr['info']['isa']

        # mark byte as invariant
        self.state.sig.append(0)

        # 3DNow instructions do not have serializing, smm, ring0,
        # or eflags effects, so we can leave it at this.

    def _explicit_operand(self, buf, opcode, operand ):
        '''
           Decode Dest, Src, or Imm operand explicitly
           declared in the opcode table
        '''
        if not opcode[operand]:
            return None

        info = { 'segment':None, 'pointer':False, 'string':False, 
             'hardcoded':False, 'implicit':False }

        info['name'] = operand
        info['access'] = opcode[operand]['access']
        info['signed'] = opcode[operand]['signed']
        info['addr_meth'] = opcode[operand]['addr_method']
        info['op_type'] = opcode[operand]['datatype']

        value = opcode[operand]['value']
        op = self.operand_decoder.decode_operand(buf, value, info)

        # TODO? if operand is 32-bit register and op_size is 16-bit... 
        return op

    def _implicit_operands(self, index, insn ):
        # append to operands
        # TODO: Generate datatypes for implicit operands
        info = { 'segment':None, 'pointer':False, 'string':False, 
             'hardcoded':True, 'implicit':True, 'name':'',
             'addr_meth':None, 'op_type':None, 'datatype':None,
             'size':None }

        op_list = IA32.implicit_operands[index]
        for o in op_list:
            inf = info.copy()
            inf['access'] = o['access']
            reg = IA32.register_factory(o['register'])
            op = Operand.Register(reg, inf)
            insn._operands.append(op)
        return

    def _stack_mod(self, insn):
        insn_type = insn.type()
        insn_group = insn.opcode().group()
        modifies_stack = False    # does insn modify stack?
        stack_mod = None    # value stack is modified by

        # yeah, yeah, i know ... "use a dict!"
        if insn_type == 'call':
            # Pop : sub address_size from ESP
            modifies_stack = True
            stack_mod = self.state.addr_size * -1
        elif insn_type == 'ret':
            # Pop : add address_size to ESP
            modifies_stack = True
            stack_mod = self.state.addr_size
        elif insn_type == 'push':
            # Pop : sub operand_size from ESP
            modifies_stack = True
            stack_mod = self.state.op_size + -1
        elif insn_type == 'pop':
            # Pop : add operand_size to ESP
            modifies_stack = True
            stack_mod = self.state.op_size
            try:
                if insn.operand(1).type() == 'stack pointer':
                    # No idea what is being popped
                    stack_mod = None
            except (IndexError, KeyError, AttributeError):
                pass
        elif insn_type == 'enter':
            # Setup stack frame: sub dest from ESP, then sub
            # src * address_size from ESP
            modifies_stack = True
            stack_mod = 0
            try:
                stack_mod = insn.operand(0).value().value() * -1
            except (IndexError, KeyError, AttributeError):
                pass
            nest = 1
            try:
                nest = insn.operand(1).value().value() + 1
            except (IndexError, KeyError, AttributeError):
                pass
            stack_mod -= nest * self.state.addr_size
        elif insn_type == 'leave':
            # Clear stack frame
            modifies_stack = True
            # ESP gets filled with EBP ... no idea what value
        elif insn_type == 'pushregs':
            # Pop flags : sub sizeof regs from ESP
            modifies_stack = True
            if self.state.op_size == 2:
                stack_mod = -16
            else:
                stack_mod = -32
        elif insn_type == 'popregs':
            # Pop flags : add sizeof regs to ESP
            modifies_stack = True
            if self.state.op_size == 2:
                stack_mod = -16
            else:
                stack_mod = -32
        elif insn_type == 'pushflags':
            # Pop flags : sub sizeof flags from ESP
            modifies_stack = True
            if self.state.op_size == 2:
                stack_mod = -2
            else:
                stack_mod = -4
        elif insn_type == 'popflags':
            # Pop flags : add sizeof flags to ESP
            modifies_stack = True
            if self.state.op_size == 2:
                stack_mod = 2
            else:
                stack_mod = 4
        elif insn_type == 'add':
            # Add: if dest is ESP, and src is Imm, add src to ESP
            try:
                if insn.operand(0).type() == 'stack pointer':
                    modifies_stack = True
                    try:
                        stack_mod = \
                         insn.operand(1).value().value()
                    except (IndexError, KeyError, \
                            AttributeError):
                        pass
            except (IndexError, KeyError, AttributeError):
                pass
        elif insn_type == 'sub':
            # Add: if dest is ESP, and src is Imm, sub src from ESP
            try:
                if insn.operand(0).type() == 'stack pointer':
                    modifies_stack = True
                    try:
                        stack_mod = \
                        insn.operand(1).value().value()\
                          * -1
                    except (IndexError, KeyError, \
                            AttributeError):
                        pass
            except (IndexError, KeyError, AttributeError):
                pass
        elif insn_type == 'inc':
            # Inc: if dest is ESP, add 1 to ESP
            try:
                if insn.operand(0).type() == 'stack pointer':
                    modifies_stack = True
                    stack_mod = 1
            except (IndexError, KeyError, AttributeError):
                pass
        elif insn_type == 'dec':
            # Dec: if dest is ESP, sub 1 from ESP
            try:
                if insn.operand(0).type() == 'stack pointer':
                    modifies_stack = True
                    stack_mod = -1
            except (IndexError, KeyError, AttributeError):
                pass
        elif insn_group == 'arith' or insn_group == 'logic' \
             or insn_group == 'load':
                 # Misc MATH/LOGIC/LOADSTORE instructions
            # If dest is ESP, mark ESP as modified
            try:
                if insn.operand(0).type() == 'stack pointer':
                    modifies_stack = True
                    # modification value is unknown
            except (IndexError, KeyError, AttributeError):
                pass

        insn.opcode()._modifies_stack = modifies_stack
        insn.opcode()._stack_mod = stack_mod
