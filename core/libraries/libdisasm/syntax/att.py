#!/usr/bin/env python2.4
###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################

'''
	libdisasm.syntax.att
	Syntax module for AT&T syntax.
'''

import base as base

class Syntax(base.Syntax):
	'''
	    libdisasm.syntax.att.Syntax
	    Formats instruction to the AT&T assembler used in GNU as:
	    	ADDRESS BYTES MNEMONIC SRC, DEST, IMM

	'''

#		'rva':False, 		# Display rva instead of offset
#		'bytes':8, 		# Max number of hex bytes to display
#		'mnem_upper':False,	# convert mnemonic to uppercase? 
#		'reg_upper':False, 	# convert register names to uppercase?
#		'op_delim':','		# operand delimiter character

	def process(self, tokens):
		''' NOP: leaves input untouched '''
		# Nothing to do for att syntax
		pass
			
	def data(self, addr):
		''' Format to DB'''
		if self._options['rva']:
			address = insn.rva()
		else:
			address = insn.offset()
		return "%08X:\n%s" % (address, str(addr))
		
	def instruction(self, insn):
		''' Format to MNEMONIC SRC, DEST, IMM '''

		if self._options['rva']:
			addr = insn.rva()
		else:
			addr = insn.offset()

		#bytes = ""
		#count = 0
		#for b in insn.bytes():
		#	bytes += "%02X " % ord(b)
		#	count += 1
		#	if count >= self._options['bytes']:
		#		break
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
		''' Add mnemonic suffix and format to MNEMONIC '''
		''' 
		    Return a string representing the opcode.
		    This is usually the prefix mnemonics followed by the
		    opcode mnemonic.
		'''
		return ' '.join( (insn.prefix_mnemonic(),
		                  insn.mnemonic()) ).lstrip()

	def operand(self, op):
		''' Add decorators required by AT&T syntax '''
		return str(op)
	
	def label(self, name):
		''' Return name as a label '''
		return name + ":"
	
	def comment(self, string):
		''' Return string as a comment '''
		return "# " + string

	def header(self):
		'''
		   Return a string describing the format of the string 
		   returned by self.line().
		'''
		return "Address %s%s Operands" % (
		      "Bytes".ljust(self._options['bytes'] * 3), 
		      "Mnemonic".ljust(self._options['mnem_len']) )



###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################
