#!/usr/bin/env python2.4

'''
	libdisasm.ia32.operand : IA32 operand decoder

	TODO: the original code had a fix for 16-bit instructions
	which verified that 32-bit registers were not used. This
	needs to be fixed in-place.
'''

import struct
from .. import isa as ISA
import isa as IA32
from .. import operand as Operand
from imm import unpack_immediate
from modrm import ModRM

class OperandDecoder(object):
	'''
	    Intel 32-bit x86 operand decoder

	    An operand factory (or absract factory, for the GOF pedants)
	    invoked by OpcodeDisassembler.
	'''
	def __init__(self, state):
		# uses the disassembler state
		self.state = state

	def _datatype_size(self, opsize):
		''' 
		    Datatype size:
		    Return the size of the datatype represented by the operand.
		'''
		sizes = { 'byte':1, 'word':2, 'dword':4, 
			'qword':8, 'dqword':16,
			'packed single real':16, 'packed double real':16,
			'simd scalar single':16, 'simd scalar double':16,
			'single real':4, 'double real':8,
			'extended real':10, 'packed bcd':4,
			'fpu environment':392,
			'fpu register set':512,
			'16-bit descriptor':4, '32-bit descriptor':6,
			'16-bit pseudo descriptor':6,
			'32-bit pseudo descriptor':6 }
		return sizes(opsize)

	def _operand_size(self, datatype):
		''' 
		    Operand size:
		    Return the size of the operand based on its datatype.
		    Note that this is the size of the operand data, not
		    the number of bytes that encodes the operand in the
		    instruction. Most of these are pointers.
		'''
		sizes = { 'byte':1, 'word':2, 'dword':4, 
			'qword':8, 'dqword':16,
			'packed single real':4, 'packed double real':4,
			'simd scalar single':4, 'simd scalar double':4,
			'single real':4, 'double real':4,
			'extended real':4, 'packed bcd':4,
			'fpu register set':4,
			'16-bit fpu state':4,
			'32-bit fpu state':4,
			'16-bit fpu environment':4,
			'32-bit fpu environment':4,
			'16-bit bounds struct':4, '32-bit bounds struct':4,
			'16-bit descriptor':4, '32-bit descriptor':6,
			'16-bit pseudo descriptor':4,
			'32-bit pseudo descriptor':4 }

		return sizes[datatype]

	def _operand_datatype(self, optype):
		'''
		   Operand datatype:
		'''
		datatypes = { 'b' : 'byte', 'w' : 'word',
			'd' : 'dword', 'q' : 'qword', 'dq' : 'dqword',
			'ps' : 'packed single real',
			'pd' : 'packed double real',
			'ss' : 'simd scalar single',
			'sd' : 'simd scalar double',
			'pi' : 'qword', 'si' : 'dword',
			'fs' : 'single real', 'fd' : 'double real',
			'fe' : 'extended real',
			'fb' : 'packed bcd',
			'fp' : 'extended real',
			'fx' : 'fpu register set'
		}

		# for the ones that depend on operand or address size,
		# we cannot (easily) use a dict.
		if optype == 'c':
			if self.state.op_size == 2:
				return 'byte'
			return 'word'
		elif optype == 'a':
			if self.state.addr_size == 2:
				return '16-bit bounds struct'
			return '32-bit bounds struct'
		elif optype == 'v':
			if self.state.op_size == 2:
				return 'word'
			return 'dword'
		elif optype == 'p':
			if self.state.addr_size == 2:
				return '16-bit descriptor'
			return '32-bit descriptor'
		elif optype == 's':
			if self.state.addr_size == 2:
				return '16-bit pseudo descriptor'
			return '32-bit pseudo descriptor'
		elif optype == 'm':
			if self.state.addr_size == 2:
				return 'word'
			return 'dword'
		elif optype == 'ft':
			if self.state.addr_size == 2:
				return '16-bit fpu state'
			return '32-bit fpu state'
		elif optype == 'fv':
			if self.state.addr_size == 2:
				return '16-bit fpu environment'
			return '32-bit fpu environment'
		else :
			return datatypes[optype]

	def _register_set(self, addr_meth, size):
		''' Determine register set:
		    Use operand address method and size to select registers.
		'''
		register_sets = {
			'E':(IA32.REG_BYTE_INDEX, IA32.REG_WORD_INDEX, 
			     IA32.REG_DWORD_INDEX),
			'M':(IA32.REG_BYTE_INDEX, IA32.REG_WORD_INDEX, 
			     IA32.REG_DWORD_INDEX),	
			'Q':(IA32.REG_MMX_INDEX,),
			'R':(IA32.REG_BYTE_INDEX, IA32.REG_WORD_INDEX, 
			     IA32.REG_DWORD_INDEX),
			'W':(IA32.REG_SIMD_INDEX,),
			'C':(IA32.REG_CTRL_INDEX,),
			'D':(IA32.REG_DEBUG_INDEX,),
			'G':(IA32.REG_BYTE_INDEX, IA32.REG_WORD_INDEX, 
			     IA32.REG_DWORD_INDEX),
			'P':(IA32.REG_MMX_INDEX,),
			'S':(IA32.REG_SEG_INDEX,),
			'T':(IA32.REG_TEST_INDEX,),
			'V':(IA32.REG_SIMD_INDEX,),
			'RR':(IA32.REG_BYTE_INDEX, IA32.REG_WORD_INDEX, 
			      IA32.REG_DWORD_INDEX),
			'RS':(IA32.REG_SEG_INDEX,),
			'RF':(IA32.REG_FPU_INDEX,),
			'RT':(IA32.REG_TEST_INDEX,) }

		reglist = register_sets[addr_meth]
		if len(reglist) == 1:
			reg_set = reglist[0]
		else:
			# NOTE: this will throw an IndexError if an opcode
			# definition has a ModRM operand of size > 4
			# associated with a general register, but that
			# shoudld never be the case.
			size -= 1
			if size > 1:
				size = 2
			reg_set = reglist[size]
		return reg_set
	
	def _segment(self, seg=None):
		seg_regs = { 	'es': IA32.REG_ES_INDEX, 
				'cs': IA32.REG_CS_INDEX,
				'ss': IA32.REG_SS_INDEX,
				'ds': IA32.REG_DS_INDEX,
				'fs': IA32.REG_FS_INDEX,
				'gs': IA32.REG_GS_INDEX }
		if not seg:
			seg = self.state.prefix_groups[2]
			if not seg or "taken" in seg:
				return None
		reg = seg_regs[seg]
		return IA32.register_factory(reg)

	def _mark_bytes(self, variant, size):
		''' append 'size' flags to signature in state: 0 for
		    an invariant byte, 1 for a variant byte. 
		'''
		self.state.sig += (variant,) * size

	def _decode_modrm_rm(self, buf, info):
		'''
		   Return a new Register or EffectiveAddress operand
		'''
		# consume modr/m byte
		buf.read(1)
		# mark modr/m byte as invariant
		self._mark_bytes(0, 1)

		modrm = self.state.modrm

		addr_meth = info['addr_meth']
		size = info['size']

		reg_set = self._register_set(addr_meth, size)
		modrm.decode(buf, reg_set, self.state.addr_size)

		if modrm.register:
			op = Operand.Register(modrm.register, info)
		else:
			# mark SIB byte as invariant
			if modrm.sib:
				self._mark_bytes(0, 1)

			# mark DISP bytes as variant
			if modrm.disp:
				self._mark_bytes(1, modrm.disp_size)

			if modrm.segment:
				info['segment'] = self._segment(modrm.segment)
			else:
				info['segment'] = self._segment()
			info['pointer'] = True

			op = Operand.EffectiveAddress(modrm.disp, modrm.base, 
				modrm.index, modrm.scale, info)

		return op

	def _decode_modrm_reg(self, info):
		'''
		   Returns a new Register operand object
		'''
		addr_meth = info['addr_meth']
		size = info['size']

		reg_set = self._register_set(addr_meth, size)
		reg = IA32.register_factory(reg_set + self.state.modrm.reg)

		return Operand.Register(reg, info)

	def _decode_nomodrm(self, buf, info):
		'''
		   Returns a new Immediate, RelativeNear, RelativeFar,
		   Offset, or SegmentOffset operand object.
		'''
		addr_meth = info['addr_meth']
		size = info['size']
		addr_size = self.state.addr_size

		if addr_meth == 'A':
			# segment:offset (far calls). Either 16:16 or 16:32.
			seg = unpack_immediate(buf, 2, False)
			off = unpack_immediate(buf, addr_size, False)
			info['pointer'] = True
			op = Operand.SegmentOffset(seg, off, info)

			# mark this operand as variant
			self._mark_bytes(1, 2 + addr_size)

		elif addr_meth == 'I':
			sign = info['signed']
			val = unpack_immediate(buf, size, sign)
			if (val.signed() > 4096 or val.signed < -4096):
			   	# use sensible defaults for signedness
				sign = False
			else:
				sign = True
			op = Operand.Immediate(val, info, sign)

			# if Optype is v, assume this is variant
			if info['op_type'] == 'v':
				self._mark_bytes(1, size)
			else:
				self._mark_bytes(0, size)
				

		elif addr_meth == 'J':
			val = unpack_immediate(buf, size, True)
			if size == addr_size:
				op = Operand.RelativeFar(val, self.state.insn, 
					info)
			else:
				op = Operand.RelativeNear(val, self.state.insn,
					info)

			# mark this operand as invariant
			self._mark_bytes(0, size)

		elif addr_meth == 'O':
			val = unpack_immediate(buf, addr_size, False)
			info['segment'] = self._segment()
			info['pointer'] = True

			op = Operand.Offset(val, info)

			# mark this operand as variant
			self._mark_bytes(1, addr_size)

		return op

	def _decode_hardcode(self, value, info):
		'''
		   Returns a new Immediate, Register, or EffectiveAddress
		   operand.
		'''
		string_regs = { 'X':(IA32.REG_ESI_INDEX, IA32.REG_SI_INDEX),
				'Y':(IA32.REG_EDI_INDEX, IA32.REG_DI_INDEX) }
		string_segs = { 'X':'ds',
				'Y':'es'}

		addr_meth = info['addr_meth']
		size = info['size']
		info['hardcoded'] = True
		if addr_meth == 'II':
			# 'Immediate' value is implicit in opcode definition
			imm = ISA.ImmediateValue(1,value,value, info['signed'])
			op = Operand.Immediate(imm, info)

		elif addr_meth == 'F':
			reg = IA32.register_factory(IA32.REG_FLAGS_INDEX)
			op = Operand.Register(reg, info)

		elif addr_meth in string_regs:
			# String destination is hard-coded in opcode definition
			# Note that the intel instruction syntax specifies
			# this as a segment:register address pair -- either
			# DS:ESI or ES:EDI -- when really what it represents
			# is an effective address, e.g. [DS:ESI].
			if self.state.addr_size == 2:
				reg_id = string_regs[addr_meth][1]
			else:
				reg_id = string_regs[addr_meth][0]

			info['string'] = True
			info['segment'] = string_segs[addr_meth]
			# NOTE: this operand applies to opcodes like MOVS.
			# Even though this is an explicit operand in the
			# opcode definition, it is not displayed during
			# disassembly ... so we make it implicit.
			info['implicit'] = True

			# base reg:
			reg = IA32.register_factory(reg_id)
			op = Operand.EffectiveAddress(None, reg, None, 1, info)

		else:
			# Register set is hard-coded in opcode definition
			reg_set = self._register_set(addr_meth, size)
			reg = IA32.register_factory(reg_set + value)
			op = Operand.Register(reg, info)

		return op

	def decode_operand(self, buf, value, info):
		'''
		   Returns a new operand object
		'''
		modrm_rm = ('E', 'M', 'Q', 'R', 'W')
		modrm_reg = ('C', 'D', 'G', 'P', 'S', 'T', 'V')
		no_modrm = ('A', 'I', 'J', 'O')
		hardcode = ('F', 'X', 'Y', 'RR', 'RS', 'RF', 'RT', 'II')

		info['datatype'] = self._operand_datatype(info['op_type'])
		info['size'] = self._operand_size(info['datatype'])

		op = None
		addr_meth = info['addr_meth']

		if addr_meth in modrm_rm:
			op = self._decode_modrm_rm(buf, info)
		elif addr_meth in modrm_reg:
			op = self._decode_modrm_reg(info)
		elif addr_meth in no_modrm:
			op = self._decode_nomodrm(buf, info)
		elif addr_meth in hardcode:
			op = self._decode_hardcode(value, info)

		return op

