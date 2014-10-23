#!/usr/bin/env python2.4

'''
	libdisasm.instruction
	
	Classes defining libdisasm instruction objects.
	
	TODO: Create an Opcode class, and move opcode-specific members
	into the Opcode class. This will make Instruction an
	InstructionAddress class which owns an Opcode.
'''
import token as Token
import address as Addr

class Opcode(object):
    '''
       libdisasm.instruction.Opcode
       Opcode definition. Future versions may share Opcode objects
       among Instruction objects to conserve memory.
       Interface:
            group()               # Instruction group classification
            type()                # Instruction type classification
            attr()                # Return opcode attributes, e.g. ring0
            modifies_stack()      # Is stack modified?
            stack_mod()           # Value stack is modified by or None
            eflags_set()          # Return condition codes set
            eflags_tested()       # Return condition codes tested
            mnemonic()            # Return mnemonic string
            output(display)       # Output instruction to display
    '''  
    def __init__(self, mnemonic, dict):
        self._mnemonic = mnemonic
        self._group = dict['group']
        self._type = dict['type']
        self._cpu = dict['cpu']
        self._isa = dict['isa']
        self._address_size = dict['address_size']
        self._operand_size = dict['operand_size']
        self._eflags_set = dict['eflags'].get('set', [])
        self._eflags_tested = dict['eflags'].get('tested', [])
        self._attr = {'ring0':dict['ring0'], 'smm':dict['smm'], 
                      'serializing':dict['serializing']}
        self._modifies_stack = dict.get('modifies_stack', False)
        self._stack_mod = dict.get('stack_mod', None)
  
    # Info interface
    def mnemonic(self):
        ''' Return the instruction mnemonic '''
        return self._mnemonic

    def group(self):
        ''' Return group or 'abstract type' classification of instruction '''
        return self._group

    def type(self):
        ''' Return type classification of instruction '''
        return self._type
    
    def cpu(self):
        return self._cpu
    
    def isa(self):
        return self._isa
    
    def address_size(self):
        return self._address_size
    
    def operand_size(self):
        return self._operand_size
    
    def attr(self, key=None):
        ''' Return opcode attributes, e.g. is this a ring0 opcode.
            'key' is the name of an attribute; if not supplied, a 
            dict of all attributes is returned. '''
        if not key:
            return self._attr.copy()
        return self._attr[key]

    def eflags_set(self):
        ''' Return condition codes set by instruction '''
        return self._eflags_set

    def eflags_tested(self):
        ''' Return condition codes checked by instruction '''
        return self._eflags_tested

    def modifies_stack(self):
        ''' Returns True if the instruction modifies the stack '''
        return self._modifies_stack

    def stack_mod(self):
        ''' Returns the value this instruction modifies the stack by:
            a positive or negative value to be added to the 
            current stack pointer. If the stack is not modified,
            or the value is not known, None is returned. Always
            call Instruction.modifies_stack() first to determine
            if the stack is modified.
        '''
        return self._stack_mod

    # TODO (no support yet) Comment interface
    # def title(self):
    # def description(self):
    # def psuedocode(self):


class Instruction(Addr.Address):
    '''
        libdisasm.instruction.Instruction
        An address containing an instruction.
        
        Interface:
            rva()                # RVA of instruction in DisasmBuf
            offset()             # Offset of instruction in DisasmBuf
            bytes()              # String of bytes in instruction
            (these first four are inherited from Address)
            signature()          # String of invariant bytes in instruction
            opcode()             # Opcode object for instruction
            type()               # Instrucition type: forwarded to opcode
            prefixes()           # Return list of prefixes
            prefix_mnemonic()    # Return prefix string
            mnemonic()           # Return mnemonic string: fwd to opcode
            operand(index)       # Return operands[index]
            operands()           # List of all operands
            explicit_operands()  # List of printable operands
            implicit_operands()  # List of unprintable operands
            output(display)      # Output instruction to display
            tokenize()           # Return list of tokens representing insn
            group()              # Return opcode group (MSL 20100618)

            
            Notes: 
                * implicit operands are those which do not normally appear in
                  assembly or disassmbly code for the instruction, but which 
                  the instruction reads are writes. These are always 
                  registers; and example is ESP in the PUSH and POP 
                  instructions.
                * invariant bytes represent a binary signature which can be
                  used to identify code patterns such as library functions.
                  These signatures consist of a list of bytes which do not
                  change across compilations or during loading; all bytes
                  which do chnage ('variant bytes') are replaced with the
                  wildcard byte 0xF4.
    '''
    __slots__ = [ '_signature', '_prefixes', '_opcode', '_operands' ] 

    def __init__(self, offset=0, rva=0, bytes="", sig="",
               mnem="", operands=(), prefixes=(), info=None):

        self._signature = sig    # invariant signature
        self._prefixes = prefixes
        self._operands = operands

        if not info:
            info = { 'cpu' : "8086", 
                     'isa' : "general purpose", 
                     'stack_mod' : None,
                     'modifies_stack' : False,
                     'address_size' : 4, 
                     'operand_size' : 4,
                     'group' : 'misc', 
                     'type': 'unknown',
                     'ring0' : False, 
                     'smm' : False, 
                     'serializing' : False,
                     'eflags':{'set':'', 'tested':''}
                    }
                      
        super(Instruction, self).__init__(offset, rva, bytes)
        self._opcode = Opcode(mnem, info)

    # Instruction interface
    def signature(self):
        ''' Return string of invariant bytes representing instruction '''
        return self._signature

    def opcode(self):
        ''' Return opcode object '''
        return self._opcode
    
    def type(self):
        ''' Return type classification of instruction 
            This wrapper allows InvalidInstruction to override. '''
        return self._opcode.type()

    def group(self):
        ''' Return group classification of instruction (MSL 20100618) '''
        return self._opcode.group()

    
    # Syntax/Output interface
    def output(self, display):
        ''' Write a representation of instruction to 'display', a
            libdisasm.output.base.Output subclass . '''
        display.instruction(self)

    def tokenize(self):
        ''' Return as list of tokens representing instruction.
            Generates the following tokens:
            [ AddressToken rva, Address Token offset,
              an AddressToken byte for each byte in insn,
              InstructionToken prefix if prefix,
              MnemonicToken mnemomic,
              an OperandToken for each operand seperated by
              InstructionToken delimiters ]
          Tokens are defined in libdisasm.token
        '''
        tokens = super(Instruction, self).tokenize()

        p = self.prefix_mnemonic()
        if not p == "":
            t = Token.InstructionToken('prefix', p)
            tokens.append(t)

        t = Token.MnemonicToken(self.mnemonic(), self.opcode())
        tokens.append(t)

        first_op = True

        for o in self._operands:
            if not first_op:
                t = Token.InstructionToken('op delimiter', ',')
                tokens.append(t)
            else:
                first_op = False
            for t in o.tokenize():
                tokens.append(t)

        return tokens

    # Disassembly interface
    def prefixes(self):
        ''' Return the list of instruction prefixes.
            Note that this includes prefixes which do not have mnemonics,
            such as operand or address size overrides. To obtain a list
            of only the prefixes with mnemonics, use prefix_mnemonic() '''
        return self._prefixes
    
    def prefix_mnemonic(self):
        ''' Return the mnemonic of printable prefixes applied
            to the instruction '''
        for p in self.prefixes():
            if p in ('lock', 'repnz', 'repz'):
                # These are all Group 1 prefixes, so only one
                # can be present
                return p
        # All other prefixes are either applied to operands
        # (e.g. segment overrides) or are implicit
        return ""

    def mnemonic(self):
        ''' Return the instruction mnemonic '''
        return self._opcode.mnemonic()

    def operand(self, index):
        ''' Return the operand at 'index' in list of operands.
            Useful on Intel for retrieving dest as insn.operand(0)
            and src as insn.operand(1)
        '''
        return self._operands[index]

    def operands(self):
        ''' Return a list of all operands (including implicit)'''
        return self._operands[:]

    def explicit_operands(self):
        ''' Return a list of explicit operands (dest, src, imm)'''
        return [o for o in self._operands if not o._info['implicit']]

    def implicit_operands(self):
        ''' Return a list of implicit operands '''
        return [o for o in self._operands if o._info['implicit']]

    # Object interface
    def __str__(self):
        ''' Return an ASCII representation of instruction.
            This is basically
                 PREFIX MNEMONIC DEST, SRC, IMM '''
        buf = self.prefix_mnemonic()
        if buf != "":
            buf += " "
        buf += self.mnemonic()

        operands = " "
        for o in self.explicit_operands():
            if operands != " ":
                operands +=  ", "
            operands += str(o)
        buf += operands

        return buf



class InvalidInstruction(Instruction):
    '''
       libdisasm.instruction.InvalidInstruction
       An instance of an instruction that could not be
       decoded. Has offset, rva, size, and bytes information
       as it will generally be stored in a list of instructions.
       An InvalidInstruction can be distinguished from a valid
       Instruction by the _opcode field, which is set to None,
       or by calling type(), which returns 'invalid'.
    '''
    __slots__ = ['_offset', '_rva', '_size', '_bytes', '_signature', 
                 '_prefixes', '_opcode', '_operands' ] 

    def __init__(self, offset=0, rva=0, bytes=""):

        self._offset = offset
        self._rva = rva
        self._size = len(bytes)    # size of instruction
        self._bytes = bytes    # bytes in instruction
        self._signature = ""

        self._opcode = None
        self._prefixes = ()
        self._operands = ()
         
    def mnemonic(self):
        return 'invalid'
 
    def type(self):
        return 'invalid'

    def group(self):
        return 'invalid'


