#!/usr/bin/env python2.4
###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################

'''
	libdisasm.token

	Tokens representing Instruction and Operand objects.
    These are intended to be used for syntax highlighting,
    and for generating assembly language syntaxes such as AT&T. 

	Instruction.token() creates:
	( AddressToken rva,
	  AddressToken offset,
	  AddressToken byte, ...,
	  InstructonToken prefix (printable), ...,
	  MnemonicToken mnemonic,
	  Operand.token(), InstructionToken operand_delimiter, ...
	)
	Labels, comments are post-processing.

	Operand.token() creates:
	( OperandToken value )				or
	( OperandToken relative )			or
	( OperandToken register )			or
	( OperandToken value, OperandToken decorator :,
	  OperandToken offset )				or
	( OperandToken register, OperandToken decorator :,
	  OperandToken offset )				or
	( OperandToken register, OperandToken decorator :,
	  OperandToken decorator [, OperandToken value (disp),
	  OperandToken decorator +, OperandToken register (base),
	  OperandToken decorator +, OperandToken register (scale),
	  OperandToken decorator *, OperandToken value (scale)
	)
	Turning an Relative to an offset is post-processing.
	  
'''
	  
class Token(object):
    '''
       libdisasm.token.Token
	   A Token representing a lexeme of a disassembled instruction,
	   such as an address, instruction mnemonic, or operand. The
	   intended use is for syntax highlighting and other formatted
	   output; actual control and data flow analysis should be
	   performed on the Instruction operands themselves.

	  Tokens can be generated for an Instruction or Operand object
	  by calling the object's tokenize() method with no arguments.

	  Component: address, instruction, or operand.
	  Type: component-dependent, e.g. rva or mnemonic.
	  Text: the pintable string representing this token.

	  Tokens may be extended to include comments, symbolic constants,
	  line labels, cross references, and so forth. Since objects are
	  represented as a list of tokens, a processing routine may
	  be applied before output to tailor the stream to a specific
	  format -- for example, to add mnemonic suffices or operand
	  prefixes for AT&T syntax, to insert additional tokens, or
	  to remove unwanted tokens.
    '''

    __slots__ = ['component', 'type', 'text']

    def __init__( self, component, type, text ):
		self.component = component
		self.type = type
		self.text = text
	
    def dict(self):
        ''' Return a representation of the token as a dict '''
        return {'component':self.component, 'type':self.type, 
			'text':self.text}

    def __str__(self):
        ''' Return the text component of the token '''
        return self.text

    def __repr__(self):
        return repr(self.dict())

class AddressToken(Token):
    ''' 
        libdisasm.token.AddressToken
        Token representing a single code or data address, i.e. a single 
        line in a disassembled listing.

        An code address will be tokenized into AddressTokens for offset, 
        rva, and each hex byte, followed by InstructionTokens and 
        OperandTokens. A data address will be tokenized into AddressTokens 
        for offset, rva, each hex byte, and each ASCII byte.

        Type: offset, rva, byte (hex or ASCII byte for dumps)
        Text: offset, address, hex or ascii byte value
        Size: size of the address object (the instruction or data) 
              for offset and rva, 1 for hex/ASCII bytes.
    '''

    __slots__ = ['size']

    def __init__(self, type, text, size):

        super(AddressToken, self).__init__( 'address', type, text )
        self.size = size

    def dict(self):
        d = super(AddressToken, self).dict()
        d['size'] = self.size
        return d


class InstructionToken(Token):
    ''' 
        libdisasm.token.InstructionToken
        Token representing a code instruction.
        
        Type: prefix, mnemonic, op delimiter
        Text: prefix name, mnemonic, delimiter text.
    '''
    def __init__(self, type, text):
        super(InstructionToken, self).__init__( 'instruction', type, 
            text )

class MnemonicToken(InstructionToken):
    ''' 
        libdisasm.token.MnemonicToken
        Token for an instruction mnemonic. Encodes information on the
        instruction type and behavior for sytax highlighting.
    '''

    __slots__ = ['group', 'type', 'cpu', 'isa', 'modifies_stack', 'ring0',
                 'smm', 'serializing' ]

    def __init__(self, text, opcode):
        super(MnemonicToken, self).__init__( 'mnemonic', text )
        self.group = opcode.group()
        self.type = opcode.type()
        self.cpu = opcode.cpu()
        self.isa = opcode.isa()

        if opcode.modifies_stack():
            self.modifies_stack = 'True'
        else:
            self.modifies_stack = 'False'

        if opcode.attr('ring0'):
            self.ring0 = 'True' 
        else:
            self.ring0 = 'False' 

        if opcode.attr('smm'):
            self.smm = 'True'
        else:
            self.smm = 'False'

        if opcode.attr('serializing'):
            self.serializing = 'True'
        else:
            self.serializing = 'False'

    def dict(self):
        d = super(MnemonicToken, self).dict()
        d['group'] = self.group
        d['type'] = self.type
        d['cpu'] = self.cpu
        d['isa'] = self.isa
        d['modifies stack'] = self.modifies_stack
        d['ring0'] = self.ring0
        d['smm'] = self.smm
        d['serializing'] = self.serializing
        return d

class OperandToken(Token):
    '''
       libdisasm.token.OperandToken
       Token for an instruction operand. A register, value, or
       relative operand will be represented by a single token.
       An offset operand will be represented by a token for the
       segment and a decorator, if the operand has a segment
       value or override, followed by the offset. An effective
       address will be composed of a number of register, offset,
       value, and decorator tokens.
       
       Type: register, offset, value, relative, decorator
       Text: register name, offset, value, rel value, []:+*
       Access: operand access string
       Name: operand name or if "" if implicit
    '''
    __slots__  = ['access', 'name']
    def __init__(self, type, text, access, name=""):
        super(OperandToken, self).__init__( 'operand', type, text )
        self.name = name
        self.access = access

    def dict(self):
        d = super(OperandToken, self).dict()
        d['name'] = self.name
        d['access'] = self.access
        return d

class RegisterToken(OperandToken):
    '''
       libdisasm.token.RegisterToken
       Token for a register operand. Encodes information on the
       type and size of the register for syntax highlighting.
    '''

    __slots__ = ['type', 'size', 'alias']

    def __init__(self, reg, access, name="" ):
        super(RegisterToken, self).__init__( 'register', 
            reg.name(), access, name )
        self.type = reg.type()
        self.size = str(reg.size())
        if reg.alias():
            self.alias = reg.alias().name()
        else:
            self.alias = ""

    def dict(self):
        d = super(RegisterToken, self).dict()
        d['type'] =  self.type
        d['size'] =  self.size
        d['alias'] =  self.alias
        return d



###################### UNCLASSIFIED // OFFICIAL USE ONLY ######################
