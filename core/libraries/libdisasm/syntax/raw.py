#!/usr/bin/env python2.4
###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################

'''
	libdisasm.syntax.raw
'''

import base as base

class Syntax(base.Syntax):
    '''
        libdisasm.syntax.raw.Syntax
        Output instructions in a pipe-delimited format.
        Note that process() does nothing.
    '''

    def process(self, tokens):
        ''' NOP: Leaves input untouched. '''
        # Nothing to do for raw syntax!
        pass
            
    def address(self, addr):
        ''' Format to rva|offset|size|bytes '''
        bytes = ' '.join(["%02X"%ord(b) for b in addr.bytes()])

        buf = "%08X|%08X|%d|%s" % (addr.rva(), addr.offset(), 
            addr.size(), bytes)
        return buf

    def data(self, addr):
        ''' Format to DATA|rva|offset|size|bytes '''
        return "DATA|%s" % (self.address(addr))

    def instruction(self, insn):
        ''' Format to CODE|rva|offset|size|bytes|mnemonic...  '''
        buf = "CODE|%s|%s" % (self.address(insn), self.mnemonic(insn))

        for o in insn.operands():
            buf += '|' + self.operand(o)

        return buf
    
    def opcode(self, op):
        return "%s|%s|%s|%s|%s|%s|%s" % (op.group(), op.type(), 
                repr(op.attr()), repr(op.modifies_stack()), 
                repr(op.stack_mod()), repr(op.eflags_set()), 
                repr(op.eflags_tested()))
            
    def mnemonic(self, insn):
        ''' Format to prefixes|mnemonic|signature|info '''
        bytes = ' '.join(["%02X"%ord(b) for b in insn.signature()])

        return "%s|%s|%s|%s" % (insn.prefixes(), insn.mnemonic(),
            bytes, self.opcode(insn.opcode()))

    def operand(self, op):
        ''' Format to operand|info '''
        return "%s|%s" % (str(op), repr(op._info))
    
    def label(self, name):
        ''' Raw syntax does not support labels, so a comment is 
            returned '''
        return self.comment("LABEL: " + name)
    
    def comment(self, string):
        ''' Return a comment line containing string '''
        return "# " + string

    def header(self):
        ''' Return description of output '''
        return "TYPE|rva|offset|size|bytes|prefixes|mnemonic|" + \
            "signature|group|type|attr|modifies stack|" + \
            "stack mod value|eflags set|eflags tested" + \
            "[[operand|operand_info]...]"
        


###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################
