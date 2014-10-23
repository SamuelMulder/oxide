#!/usr/bin/env python2.4
'''
	libdisasm.ia32.modrm : Decode ModRM and SIB bytes
'''

import isa as IA32
from imm import unpack_immediate


# Mod R/M and SIB ========================================================
class ModRM(object):
	'''
	    ModR/M byte
	'''
	# Mod R/M fields
	mod = 0
	reg = 0
	rm = 0
	# Decoded ModR/M components
	register = None
	base = None
	index = None
	scale = None
	disp = None
	disp_size = None
	segment = None
	sib = False
	# constants
	class RM(object):
		SIB = 4
		NO_REG = 5
	class MOD(object):
		NO_DISP = 0
		DISP8 = 1
		DISP32 = 2
		DISP16 = 2
		REG_ONLY = 3
	class RM16(object):
		BXSI = 0
		BXDI = 1
		BPSI = 2
		BPDI = 3
		SI = 4
		DI = 5
		BP = 6
		BX = 7

	class SIB(object):
		'''
		    SIB (scale, index, base) byte
		'''
		# SIB fields
		scale = 0
		index = 0
		base = 0
		# Decoded SIB components
		base_reg = None
		index_reg = None
		scale_val = None
		disp = None
		disp_size = None
		segment = None
		# constants
		NO_BASE = 0
		NO_INDEX = 4
		EBP_BASE = 5

		def __init__(self, byte, mod):
			self._unpack_byte(byte)
			if not mod:
				self.disp_exists = False
			else:
				self.disp_exists = True

		def _unpack_byte(self, byte):
			byte = ord(byte)
			self.scale = (byte >> 6) & 3 	# top 2 bits
			self.index = (byte >> 3) & 7 	# middle 3 bits
			self.base = byte & 7  		# bottom 3 bits

		def decode(self, buf):
			if self.base == self.EBP_BASE and not self.disp_exists:
				# if ModR/M did not create a displacement 
				# (! mod) get 4-byte unsigned disp
				self.disp = unpack_immediate(buf, 4, False)
				self.disp_size = 4
			else:
				self.base_reg = \
				     IA32.register_factory(self.base + 1)

			self.scale_val = 1 << self.scale
			if self.index != self.NO_INDEX:
				self.index_reg = \
				     IA32.register_factory(self.index + 1)

	def __init__(self, byte):
		self._unpack_byte(byte)

	def _unpack_byte(self, byte):
		byte = ord(byte)
		self.mod = (byte >> 6) & 3 	# top 2 bits
		self.reg = (byte >> 3) & 7 	# middle 3 bits
		self.rm = byte & 7  		# bottom 3 bits

	def _decode_16(self, buf):
		# format: base, index, seg
		rm_regs = (
			( IA32.REG_BX_INDEX, IA32.REG_SI_INDEX, None ),
			( IA32.REG_BX_INDEX, IA32.REG_DI_INDEX, None ),
			( IA32.REG_BP_INDEX, IA32.REG_SI_INDEX, "ss" ),
			( IA32.REG_BP_INDEX, IA32.REG_DI_INDEX, "ss" ),
			( IA32.REG_SI_INDEX, None, None ),
			( IA32.REG_DI_INDEX, None, None ),
			( IA32.REG_BX_INDEX, None, None ),
			( IA32.REG_BP_INDEX, None, "ss" ) )

		self.base = IA32.register_factory(rm_regs[self.rm][0])

		idx = rm_regs[self.rm][1]
		if idx:
			self.index = IA32.register_factory(idx)

		if self.mod == ModRM.MOD.DISP8:
			# get 1-byte signed displacement
			self.disp = unpack_immediate(buf, 1, True)
			self.disp_size = 1

		elif self.mod == ModRM.MOD.DISP16:
			# get 2-byte unsigned displacement
			self.disp = unpack_immediate(buf, 2, False)
			self.disp_size = 2

		elif self.mod == ModRM.MOD.NO_DISP and \
		     self.rm == ModRM.RM16.BP:
		     # special case: there is no [BP] case, instead it
		     # decodes to disp16 with no register
			self.base = None
			# get 2-byte unsigned displacement
			self.disp = unpack_immediate(buf, 2, False)
			self.disp_size = 2

		seg = rm_regs[self.rm][2]
		if seg:
			self.segment = seg

	def _decode_base(self, buf):
		if self.rm == ModRM.RM.SIB:
			# RM = 100
			self.sib = True
			sib = ModRM.SIB(buf.read(), self.mod)
			sib.decode(buf)
			self.base = sib.base_reg
			self.index = sib.index_reg
			self.scale = sib.scale_val
			self.disp = sib.disp
			self.disp_size = sib.disp_size
			if sib.segment:
				self.segment = sib.segment

		else:
			# RM encodes a general register
			self.base = IA32.register_factory(IA32.REG_DWORD_INDEX + self.rm )

	def decode(self, buf, reg_set, addr_size):
		'''
		    Decode ModR/M byte, using mod and r/m fields.
		    Reg/opcode extension field is handled elsewhere.
		    Does not consume the ModR/M byte from buf, but
		    DOES consume SIB and displacement bytes.
		'''
		if self.mod == ModRM.MOD.REG_ONLY:
			# MOD = 11
			self.register = IA32.register_factory(reg_set + self.rm)
			return

		if addr_size == 2:
			return self._decode_16(buf)

		if self.mod == ModRM.MOD.NO_DISP:
			# MOD = 00
			if self.rm == ModRM.RM.NO_REG:
				# RM = 101
				# read a unsigned dword from buffer
				self.disp = unpack_immediate(buf, 4, False)
				self.disp_size = 4
			else:
				self._decode_base(buf)
		else:
			self._decode_base(buf)

			# NOTE: since mod > 0 in these cases, SIB.decode()
			#       never creates a displacement.
			if self.mod == ModRM.MOD.DISP8:
				# get signed byted into displacement
				self.disp = unpack_immediate(buf, 1, True)
				self.disp_size = 1
			else:
				# get unsigned dword into displacement
				self.disp = unpack_immediate(buf, 4, False)
				self.disp_size = 4
