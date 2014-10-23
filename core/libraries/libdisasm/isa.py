#!/usr/bin/env python2.4

'''
	libdisasm.isa

	Definitions of generic ISA elements (currently 
	Register and ImmediateValue). These mostly exist
	to make possible EffectiveAddress operands, which 
	contain up to two Registers and one ImmediateValue.
'''

class Register(object):
	'''
	   libdisasm.isa.Register

	   A generic register object. Used by Register and
	   EffectiveAddress operand objects.
	   
	   Interface:
	   	name()			# register mnemonic
	   	size()			# Size of register in bytes
	   	type()			# String with types(s) of register
	   	id()				# Internal register ID number
	   	alias()
	   	alias_shift()
	   
	   Notes:
	   		* The register Alias is another Register instance 
	   		  which the current register is an alias for. Some
	   		  aliases are straightforward: AL and AX are aliases
	   		  for EAX, with their size determine how many of the
	   		  low-order bytes of EAX they alias to. Other aliases,
	   		  such as AH, are left-shifted into EAX. The left shift
	   		  value is provided in the alias_shift() method.
	'''
	
	__slots__ = ['_id', '_name', '_size', '_type', '_alias', '_shift']

	def __init__(self, descr, alias=None, id=0):
		''' Create a Register object from a dict 'descr'. The dict is
		    expected to define string 'size', tuple 'type,
		    and string 'name'
		'''
		self._id = id
		self._name = descr['name']
		self._size = descr['size']
		self._type = descr['type']
		self._alias = alias
		if self._alias:
			self._shift = descr['alias_shift']
	def name(self):
		''' Return register mnemonic string '''
		return self._name

	def size(self):
		''' Return size of the register in bytes '''
		return self._size

	def type(self):
		''' Return the type string describing the register '''
		return self._type

	def id(self):
		''' Return the (internal) id of this register. This can 
		    be used for identity checks. '''
		return self._id

	def alias(self):
		''' Return the register object that this is an alias for. '''
		return self._alias

	def alias_shift(self):
		''' Return the number of bits to right shift the value in
		    'alias' by to get the value in this register. this
		    is used by VMs which store values in the core
		    [aliased] registers, e.g. the value is stored in
		    'ax', but when 'ah' is read ax must be right-shifted
		    8 bits, and when 'ah' is written its value must be
		    left-shifted 8 bits before being stored in ax. '''
		return self._shift

	def __str__(self):
		''' Return the register mnemonic string '''
		return self.name()


class ImmediateValue(object):
	'''
	   libdisasm.isa.ImmediateValue
	   
	   A generic immediate value object. Used in Immediate and
	   Effective Address operands. Can be subclassed to
	   support symbolic constants.
	   
	   Interface:
	   	value()				# signed() or unsigned() based on is_signed()
	   	signed()				# signed representstion of value
	   	unsigned()			# unsigned representation of value
	   	size()				# size of value in bytes
	   	is_signed()			# is the value signed?
	   	set_signed(boolean)	# Set whether this value is signed
	   	
	   Notes:
			* It is easier to get the signed and unsigned values of
			  a sequences of bytes when actually doing the unpacking
			  than to do it as-needed in this class. This both signed and
			  unsigned values are unpacked during disassembly, and stored
			  in this object with the is_signed flag set according to
			  context. This allows the user to switch between signed and
			  unsigned representations of an immediate value easily.
	'''

	def __init__(self, size, unsigned_val, signed_val, is_signed=False):
		self._size = size
		self._value = unsigned_val
		self._signed_value = signed_val
		self._is_signed = is_signed
	
	def value(self):
		''' Return the default representation of the value: calls
		    signed() if the is_signed() flag is set, unsigned() otherwise. 
		'''	
		if self._is_signed:
			return self._signed_value
		return self._value

	def signed(self):
		''' Return the signed representation of the value. '''
		return self._signed_value

	def unsigned(self):
		''' Return the unsigned representation of the value. '''
		return self._value
	
	def size(self):
		''' Return the size of the value in bytes. '''
		return self._size

	def is_signed(self):
		''' Return True if the value is signed, False otherwise. '''
		return self._is_signed

	def set_signed(self, signed=True):
		''' Set the value of the is_signed flag. '''
		self._is_signed = signed

	def __str__(self):
		''' Return a decimal representation of signed values,
		    and a hexadecimal representation of unsigned values. '''
		if self._is_signed:
			# force signed decimal representation
			return str(self.value())
		else:
			# return the raw hex representation
			return "0x%X" % self._value

