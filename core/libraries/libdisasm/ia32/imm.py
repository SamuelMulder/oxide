#!/usr/bin/env python2.4

'''
	libdisasm.ia32.imm : Read immediate values from little-endian buf
'''

import struct
from .. import isa as ISA


def unpack_immediate(buf, size, signed=False):
	''' Unpack immediate data
	    Read 'size' bytes from buf and unpack into an
	    isa.Immediate object.
	'''
	unpack_str = ( None, 'B', 'H', None, 'L', None, None, None, 'Q' )


	if size > len(unpack_str) or not unpack_str[size]:
		raise AssertionError, 'eh wot?'

	unsigned_fmt = '<' + unpack_str[size]
	signed_fmt = '<' + unpack_str[size].lower()

	unpack_buf = buf.read(size)
	u_val = struct.unpack(unsigned_fmt, unpack_buf)[0]
	s_val = struct.unpack(signed_fmt, unpack_buf)[0]

	return ISA.ImmediateValue(signed, u_val, s_val, signed)
	

