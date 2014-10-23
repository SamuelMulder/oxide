#!/usr/bin/env python2.4
###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################

'''
	libdisasm.syntax.base
'''

class Syntax(object):
	'''
	    libdisasm.syntax.base.Syntax
	    Formats an instruction or operand according to a specific
	    syntax, e.g. Intel or AT&T.

	    Usage:
	    	# process a list of tokens to match syntax requirements
	    	syntax.process(tokens)

		# get a string representing the instruction address
		line = syntax.line(instruction)

		# get a string representing the mnemonic
		mnem_str = syntax.mnemonic(instruction)

		# get a string representing an operand
		op_str = syntax.operand(operand)

	'''

	_default_options = {
	# TODO: address, mnemonic, operand, comment position?
	# TODO: fix relative?
		'rva':False, 		# Display rva instead of offset
		'bytes':8, 		# Max number of hex bytes to display
		'mnem_upper':False,	# convert mnemonic to uppercase? 
		'reg_upper':False, 	# convert register names to uppercase?
		'op_delim':', ',	# operand delimiter character
		'mnem_len':12		# max expected mnemonic length
		# the longest mnemonic in x86 is 'prefetchnta'
	}

	def __init__(self, options=None):
		self._options = self._default_options.copy()

		if options:
			self._options.update(options)

	def process(self, tokens):
		'''
		   Process a list of tokens (libdisasm.token), adding
		   decorators tokens and mnemonic prefixes or suffixes
		   as appropriate. The list of tokens is modified in-place.
		'''
		raise NotImplementedError, 'Syntax.process() is virtual'
			
	def data(self, addr):
		''' 
		    Return a string representing the data address.
		    Usually this is the rva or address and the hex bytes.
		'''
		raise NotImplementedError, 'Syntax.data() is virtual'

	def instruction(self, insn):
		''' 
		    Return a string representing the instruction address.
		    Usually this is the rva or address, hex bytes, mnemonic,
		    and all explicit operands.
		    TODO: Support data address lines?
		'''
		raise NotImplementedError, 'Syntax.instruction() is virtual'
			
	def mnemonic(self, insn):
		''' 
		    Return a string representing the opcode.
		    This is usually the prefix mnemonics followed by the
		    opcode mnemonic.
		'''
		raise NotImplementedError, 'Syntax.mnemonic() is virtual'

	def operand(self, op):
		''' 
		    Return a string representing the operand.
		    Usually this is just str(op).
		'''
		raise NotImplementedError, 'Syntax.operand() is virtual'
	
	def label(self, name):
		'''
		   Return a string represnting the address label.
		   Usually this is just 'name:\n'.
		'''
		raise NotImplementedError, 'Syntax.label() is virtual'
	
	def comment(self, string):
		'''
		   Return a string represnting the comment.
		   Usually this is just '# string'.
		   Note that a comment means 'text ignored when parsing
		   the output file', thus for RAW syntax it will be a
		   line starting with #.
		'''
		raise NotImplementedError, 'Syntax.comment() is virtual'
	
	def header(self):
		'''
		   Return a string describing the format of the string 
		   returned by self.line().
		'''
		raise NotImplementedError, 'Syntax.header() is virtual'



###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################
