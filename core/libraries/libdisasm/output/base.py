#!/usr/bin/env python2.4

'''
	libdisasm.output.base

	Base classes for display and file output
'''

class Output(object):
	'''
	    libdisasm.output.base.Output
	'''
	def __init__(self, syntax):
		self._syntax = syntax

	def instruction(self, insn):
		# use syntax.instruction(insn) to generate string
		raise NotImplementedError, 'Output.instruction() is virtual'

	def data(self, addr):
		# use syntax.data(insn) to generate string
		raise NotImplementedError, 'Output.data() is virtual'
	
	def label(self, name):
		# use syntax.label(insn) to generate string
		raise NotImplementedError, 'Output.label() is virtual'
	
	def comment(self, string):
		# use syntax.comment(insn) to generate string
		raise NotImplementedError, 'Output.comment() is virtual'


