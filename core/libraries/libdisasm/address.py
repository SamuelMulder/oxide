#!/usr/bin/env python2.4

'''
	libdisasm.address
'''

import token as Token

class Address(object):
    '''
	   libdisasm.address.Address
       An address object, containing offset, rva, and size info.
       An Address object represents a data address, and is subclassed
       to represent a code address.
       
       Interface:
           offset()    # Offset of address in file or None
           rva()       # Load address in memory or None
           size()      # Size of address object in bytes
           bytes()     # String of bytes at address
	'''
    __slots__ = ['_rva', '_offset', '_size', '_bytes' ]

    def __init__(self, offset=0, rva=0, bytes=""):

		self._offset = offset
		self._rva = rva
		self._size = len(bytes)	# size of instruction
		self._bytes = bytes	# bytes in instruction

	# Binary interface
    def offset(self):
		''' Return the Address offset '''
		return self._offset

    def rva(self):
		''' Return the Address relative virtual address '''
		return self._rva

    def bytes(self):
		''' Return a string containing the raw bytes of the Address '''
		return self._bytes
	
    def size(self):
		''' Return the number of bytes in the Address '''
		return self._size

	# Syntax/Output interface
    def output(self, display):
		'''  Output Address to display '''
		display.data(self)

    def tokenize(self):
        ''' 
		    Return a list of tokens representing the Address.
		    Generates the following tokens:
		    ( AddressToken rva, Address Token offset,
		      an AddressToken byte for each byte in insn)
        '''
        tokens = []

        t = Token.AddressToken('rva', '%08X' % self._rva, 
            str(self._size) )
        tokens.append(t)

        t = Token.AddressToken('offset', '%08X' % self._offset, 
            str(self._size) )
        tokens.append(t)

        tokens += [Token.AddressToken('byte', '%02X' % ord(b), str(1))\
               for b in self.bytes()]

        return tokens


    # Object interface
    def __str__(self):
        ''' Return a string representing address as hex bytes. '''
        lines = []
        bytes = self.bytes()

        for i in xrange(0, self._size(), 16):
            slice = bytes[i:i+16]
            hx = ' '.join(["%02X"%ord(b) for b in slice])
            asc = slice.translate( ''.join([ (b > 31 and b < 127) \
                and chr(b) or '.' for b in range(256) ]) )
            lines.append("%-48s%s\n", hx, asc) 

        return ''.join(lines)
