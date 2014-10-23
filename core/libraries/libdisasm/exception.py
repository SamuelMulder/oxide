#!/usr/bin/env python2.4

'''
	libdisasm.exception
	
	Exceptions thrown by the disassembler
'''

class DecodeError(Exception):
	'''
	   Instruction decoding error
	   Thrown by opcode disassemblers.
	   	Message : a description of the error
	   	Table : the last opcode table used for lookup
	   	Byte : the byte used as an index into the table
	   	Offset : the buffer position where the error occurred
	   	Start : the buffer position where decoding started
	'''
	def __init__(self, start, offset, table, byte, message):
		self._start = start		# offset of first byte decoded
		self._offset = offset	# offset where error occurred
		self._table = table		# table where error occurred
		self._byte = byte		# value of byte causing error
		self._message = message

	def __str__(self):
		return  self._message + " Last table: " + self._table + \
		        " Byte: " + hex(self._byte) + \
			" Buffer position: " + hex(self._offset) + \
			" Start position: " + hex(self._start)

