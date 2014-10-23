#!/usr/bin/env python2.4
'''
	libdisasm.output.ascii
	Outputs ASCII to STDOUT, a list of lines, or a file.

	Base classes for display and file output
'''

import sys
import base as output

class Ascii(output.Output):
	'''
	   libdisasm.output.ascii.ascii
	   Base class for generating output. 
	   Due to the simplicity of ASCII, this is largely an example.
	'''

	def instruction(self, insn):
		return self._syntax.instruction(insn)

	def data(self, addr):
		return self._syntax.data(addr)

	def label(self, name):
		return self._syntax.label(name)

	def comment(self, string):
		return self._syntax.comment(string)


	
class Stdout(Ascii):
	'''
	    libdisasm.output.ascii.Stdout
	    Writes the output of Syntax directly to STDOUT
	'''
	def __init__(self, syntax):
		super(Stdout, self).__init__(syntax)

	def instruction(self, insn):
		sys.stdout.write(super(Stdout,self).instruction(insn) + '\n')

	def data(self, addr):
		sys.stdout.write(super(Stdout,self).data(addr) + '\n')

	def label(self, name):
		sys.stdout.write(super(Stdout,self).label(name) + '\n')

	def comment(self, string):
		sys.stdout.write(super(Stdout,self).comment(string) + '\n')

class List(Ascii):
	'''
	    libdisasm.output.ascii.List
	    Appends the output of Syntax to a list.
	'''
	def __init__(self, syntax, list):
		super(List, self).__init__(syntax)
		self._list = list

	def instruction(self, insn):
		self._list.append(super(List, self).instruction(insn))

	def data(self, addr):
		self._list.append(super(List, self).data(addr))

	def label(self, name):
		self._list.append(super(List, self).label(name))

	def comment(self, string):
		self._list.append(super(List, self).comment(string))
		

class File(Ascii):
	'''
	    libdisasm.output.ascii.File
	    Writes the output of Syntax to file.
	'''
	def __init__(self, syntax, file):
		super(File, self).__init__(syntax)
		self._file = file

	def instruction(self, insn):
		self._file.write(super(File, self).instruction(insn) + '\n')

	def data(self, addr):
		self._file.write(super(File, self).data(addr) + '\n')

	def label(self, name):
		self._file.write(super(File, self).label(name) + '\n')

	def comment(self, string):
		self._file.write(super(File, self).comment(string) + '\n')

