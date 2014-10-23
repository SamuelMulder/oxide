#!/usr/bin/env python2.4
###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################

'''
	libdisasm.syntax.native
	Syntax module for a typical disassembled listing.
'''

import base as base

class Syntax(base.Syntax):
	'''
	    libdisasm.syntax.native.Syntax
	    Formats instruction to a typical Intel disassembled listing:
	    	ADDRESS BYTES MNEMONIC DEST, SRC, IMM

	'''

	def process(self, tokens):
		''' NOP: leaves input untouched '''
		# Nothing to do for native syntax
		pass
			
	def data(self, addr):
		''' Format to ADDRESS HEXDUMP'''
		if self._options['rva']:
			address = insn.rva()
		else:
			address = insn.offset()
		return "%08X:\n%s" % (address, str(addr))
		
	def instruction(self, insn):
		''' Format to ADDRESS BYTES MNEMONIC DEST, SRC, IMM '''

		if self._options['rva']:
			addr = insn.rva()
		else:
			addr = insn.offset()

		bytes = ' '.join(["%02X"%ord(b) for b in \
			insn.bytes()[:self._options['bytes']] ])

		mnem = self.mnemonic(insn)
		
		buf = "%08x %s %s " % (addr, 
		      bytes.ljust(self._options['bytes'] *3), 
		      mnem.ljust(self._options['mnem_len']))

		buf += self._options['op_delim'].join(
			[self.operand(o) for o in insn.explicit_operands()] )

		return buf
		      
			
	def mnemonic(self, insn):
		''' 
		    Return a string representing the opcode.
		    This is usually the prefix mnemonics followed by the
		    opcode mnemonic.
		'''
		return ' '.join( (insn.prefix_mnemonic(),
		                  insn.mnemonic()) ).lstrip()

	def operand(self, op):
		''' 
		    Return a string representing the operand.
		    Usually this is just str(op).
		'''
		return str(op)
	
	def label(self, name):
		''' Return name as a label '''
		return name + ":"
	
	def comment(self, string):
		''' Return string as a comment '''
		return "; " + string

	def header(self):
		'''
		   Return a string describing the format of the string 
		   returned by self.line().
		'''
		return "Address %s%s Operands" % (
		      "Bytes".ljust(self._options['bytes'] * 3), 
		      "Mnemonic".ljust(self._options['mnem_len']) )



###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################
