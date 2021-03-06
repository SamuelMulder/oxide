#!/usr/bin/env python2.4
'''
   libdisasm.operand
   
   Instruction operand representation.
'''

import isa as ISA
import token as Token

class Operand(object):
    '''
	   libdisasm.operand.Operand
       Instruction operand base class.
       
       Interface:
         type()        # operand type string
         datatype()    # operand datatype string
         size()        # operand datatype size in bytes
         access()      # rwx access by instruction
         implicit()    # is operand implicit?
         segment_reg() # segment register override, or None
         info()        # return a copy of the info dict
         tokenize()    # return list of tokens representing operand
         
       Notes:
           * access is a typical 'rwx' permissions string. An 'r' indicates
             the operand is read by the instruction, a 'w' indicates the
             operand is written by the instruction, and an 'x' indicates
             the operand is executed by the instruction (e.g. a jmp or call).
             If an access method is not used, a '-' appears in its place; thus
             a jmp target, which is read and then and executed, will have access
             'r-x'. 
           * implicit operands are registers which do not appear in the ISA
             assembly language representation of the instruction, but which
             are read or written by the instruction. The best example of this
             is the stack pointer (ESP) which is modified by PUSH and POP
             instructions. Keeping track of implicit operands can aid in proper
             dataflow analysis. 
           * the _info dict can be used by the disassembler to 
             associate arbitrary flags with operand. The public
             interface only allows a copy of this dict to be retrieved.
    '''
    
    __slots__ = ['_info']

    def __init__(self, info=None):
        if info:
            self._info = info
        else:
            self._info = { 'type' : "operand",
                           'datatype' : 'dword',
                       'access' : "---",
                       'implicit' : False,
                       'hardcoded' : False,
                       'segment' : None
                     }
     
    def type(self):        
        ''' Return operand type string, e.g. 'register'.  '''
        return self._info['type']

    def datatype(self):
        ''' Return operand datatype string, e.g. 'dword'. '''
        return self._info['datatype'][0]

    def size(self):
        ''' Return operand datatype size in bytes. '''
        return self._info['datatype'][1]

    def access(self):
        ''' Return rwx permissions string specifying how the
            instruction access operand:
                r--    insn reads operand
                -w-    insn writes operand
                --x    insn executes (jmp/call) operand
        '''
        return self._info['access']

    def implicit(self):
        ''' Return True if the operand is implicit '''
        return self._info['implicit']

    def segment_reg(self):
        ''' Return a Register object for the segment register override,
            or None if no override is present. These overrides are
            generated by segment override prefixes in the instruction.'''
        return self._info['segment'].name()

    def info(self):
        ''' Return a copy of the operand info dict. '''
        return self._info.copy()

    def tokenize(self):
        ''' Return a list of tokens representing the operand. '''
        # virtual method
        pass

    def _sign(self, val):
        ''' Private method for use in subclasses having immediate values. '''
        # determine if immediate is signed based in a rough heuristic.
        # TODO: find some way to make this an option!
        if val.size() == 1 or \
           (val.signed() <= 0 and val.signed() > -4096):
               # display in signed decimal
            return True
        else:
               # display in unsigned hexadecimal
            return False

class Immediate(Operand):
    '''
       libdisasm.operand.Immediate
    '''
    __slots__ = ['_value']

    def __init__(self, value, info=None, sign=None):
        ''' value : scalar value. instance of libdisasm.isa.Immediate .
            info : dictionary containing operand flags.'''
        try:
            value.value()
        except AttributeError, e:
            raise TypeError,'value must be an isa.Immediate'

        self._value = value
        super(Immediate, self).__init__(info)
        self._info['type'] = 'immediate'

        if sign is None:
            sign = self._sign(value)
        value.set_signed(sign)

    def value(self):
        return self._value
    
    def signed(self):
        return self._value.is_signed()
    
    def __str__(self):
        return str(self._value)

    def tokenize(self):
        name = self._info.get('name', '')
        access = self._info['access']
        t = Token.OperandToken('value', str(self), access, name)
        return (t,)

class Relative(Immediate):
    '''
       libdisasm.operand.Relative
       Relative operands contain a reference to the Instruction object
       owning them in order to calculate their offset or address
    '''
    __slots__ = ['_insn']
    def __init__(self, value, insn, info=None):
        ''' value : pc-rel value. instance of libdisasm.isa.Immediate .
            info : dictionary containing operand flags.'''
        # relative operands are always signed
        super(Relative, self).__init__(value, info, True)
        self._insn = insn
        self._info['type'] = 'relative'
        self._info['signed'] = True

    def offset(self):
        ''' Compute the buffer offset of the operand based on the
            buffer offset of the instruction
        '''
        return self._insn.offset() + self._insn.size() + \
            self.value().signed()
    def rva(self):
        return self._insn.rva() + self._insn.size() + \
            self.value().signed()

    def tokenize(self):
        name = self._info.get('name', '')
        access = self._info['access']
        t = Token.OperandToken('relative', str(self), access, name)
        return (t,)

class RelativeNear(Relative):
    '''
       libdisasm.operand.RelativeNear
    '''
    def __init__(self, value, insn, info=None):
        ''' value : pc-rel value. instance of libdisasm.isa.Immediate .
            info : dictionary containing operand flags.'''
        super(RelativeNear, self).__init__(value, insn, info)
        self._info['type'] = 'relative near'

class RelativeFar(Relative):
    '''
       libdisasm.operand.RelativeFar
    '''
    def __init__(self, value, insn, info=None):
        ''' value : pc-rel value. instance of libdisasm.isa.Immediate .
            info : dictionary containing operand flags.'''
        super(RelativeFar, self).__init__(value, insn, info)
        self._info['type'] = 'relative far'

class Offset(Immediate):
    '''
       libdisasm.operand.Offset
    '''
    def __init__(self, offset, info=None):
        ''' offset : offset. instance of libdisasm.isa.Immediate .
            info : dictionary containing operand flags.'''
        try:
            offset.value()
        except AttributeError, e:
            raise TypeError,'offset must be an isa.Immediate'

        sign = self._sign(offset)
        super(Offset, self).__init__(offset, info, sign)

        self._info['type'] = 'offset'

    def offset(self):
        return self._value

    def __str__(self):
        offset = "0x%08X" % self.offset().value()
        if self._info['segment']:
            return self._info['segment'].name() + ':' + offset
        return offset

    def tokenize(self):
        tokens = []
        name = self._info.get('name', '')
        access = self._info['access']
        offset = "0x%08X" % self.offset().value()
        reg = self._info['segment']
        if reg:
            t = Token.RegisterToken(reg, access, name)
            tokens.append(t)
            t = Token.OperandToken('decorator', ':', access, name)
            tokens.append(t)

        t = Token.OperandToken('offset', offset, access, name)
        tokens.append(t)
        return tokens

class SegmentOffset(Immediate):
    '''
       libdisasm.operand.SegmentOffset
    '''
    __slots__ = ['_segment']

    def __init__(self, segment, offset, info=None):
        ''' segment : segment. instance of libdisasm.isa.Immediate .
            offset : offset. instance of libdisasm.isa.Immediate .
            info : dictionary containing operand flags.'''
        try:
            segment.value()
        except AttributeError, e:
            raise TypeError,'segment must be an isa.Immediate'
        try:
            offset.value()
        except AttributeError, e:
            raise TypeError,'offset must be an isa.Immediate'

        # segment:offset values are never signed.
        super(SegmentOffset, self).__init__(offset, info, False)
        self._segment = segment

        self._info['type'] = 'segment:offset'

    def segment(self):
        return self._segment

    def offset(self):
        return self._value

    def __str__(self):
        return hex(self.segment().value()) + ':' + \
               hex(self.offset().value())

    def tokenize(self):
        tokens = []
        name = self._info.get('name', '')
        access = self._info['access']
        segment = "0x%04X" % self.segment().value()
        offset = "0x%08X" % self.offset().value()

        t = Token.OperandToken('value', segment, access, name )
        tokens.append(t)
        t = Token.OperandToken('decorator', ':', access, name)
        tokens.append(t)
        t = Token.OperandToken('offset', offset, access, name)
        tokens.append(t)
        return tokens

class Register(Operand):
    '''
       libdisasm.operand.Register
    '''
    __slots__ = ['_reg']
    def __init__(self, reg, info=None):
        ''' reg : register. instance of libdisasm.isa.Register .
            info : dictionary containing operand flags.'''
        super(Register, self).__init__(info)
        self._reg = reg
        self._info['type'] = 'register'

    def name(self):
        return self._reg.name()

    def size(self):
        return self._reg.size()

    def type(self):
        return self._reg.type()

    def id(self):
        return self._reg.id()

    def alias(self):
        return self._reg.alias()

    def alias_shift(self):
        return self._reg.alias_shift()

    def __str__(self):
        return str(self._reg)

    def tokenize(self):
        name = self._info.get('name', '')
        access = self._info['access']
        t = Token.RegisterToken(self._reg, access, name)
        return (t,)

class EffectiveAddress(Operand):
    '''
       libdisasm.operand.EffectiveAddress
    '''
    __slots__ = ['_disp', '_base', '_index', '_scale']

    def __init__(self, disp, base, index, scale=1, info=None):
        ''' disp : displacement. instance of libdisasm.isa.Immediate .
            base : base. instance of libdisasm.isa.Register .
            index : index. instance of libdisasm.isa.Register .
            scale : scale. Integer in (1, 2, 4, 8).
            info : dictionary containing operand flags.'''
        if disp is not None:
            try:
                disp.value()
            except AttributeError, e:
                raise TypeError,'disp must be an isa.Immediate'
            disp.set_signed(self._sign(disp))

        super(EffectiveAddress, self).__init__(info)

        self._disp = disp 
        self._base = base
        self._index = index
        if scale:
            self._scale = scale
        else:
            self._scale = 1
        self._info['type'] = 'effective address'
    
    def disp(self):
        ''' Return integer value for displacement '''
        return self._disp

    def base(self):
        ''' Return ISA.Register object for base '''
        return self._base

    def index(self):
        ''' Return ISA.Register object for index '''
        return self._index

    def scale(self):
        ''' Return integer value if scale (1, 2, 4, 8) '''
        return self._scale

    def __str__(self):
        # disp + base + index * scale
        seg = ''
        if self._info['segment']:
            # changed by matt 20070321
            seg = self._info['segment'].name() + ':'
            #seg = self._info['segment'] + ':'
            
        exp = ''
        if self._disp:
            exp = str(self._disp)

        if self._base:
            if exp == '':
                exp = str(self._base)
            else:
                exp += ' + ' + str(self._base)

        idx = ''
        if self._index:
            idx = str(self._index)

        if self._scale != 1:
             idx += ' * ' + str(self._scale)

        if len(exp) and len(idx):
            exp += ' + ' + idx
        else:
            exp += idx

        return seg + '[' + exp + ']'

    def tokenize(self):
        name = self._info.get('name', '')
        access = self._info['access']
        seg = self._info['segment']
        tokens = []

        if seg:
            t = Token.RegisterToken(seg, access, name)
            tokens.append(t)
            t = Token.OperandToken('decorator', ':', access, name)
            tokens.append(t)
        t = Token.OperandToken('decorator', '[', access, name)
        tokens.append(t)

        disp = self._disp
        first_expr = False
        # FIXME: should the isa object handle token?
        if disp and disp.size() == 1:
            t = Token.OperandToken('value', str(disp), access, name)
            tokens.append(t)
        elif disp:
            t = Token.OperandToken('offset', str(disp), access, 
                        name)
            tokens.append(t)
        else:
            first_expr = True

        base = self._base
        if base:
            if not first_expr:
                t = Token.OperandToken('decorator', '+', 
                            access, name)
                tokens.append(t)
            else:
                first_expr = False

            t = Token.RegisterToken(base, access, name)
            tokens.append(t)

        index = self._index
        if index:
            if not first_expr:
                t = Token.OperandToken('decorator', '+', 
                            access, name)
                tokens.append(t)
            else:
                first_expr = False

            t = Token.RegisterToken(index, access, name)
            tokens.append(t)
            
            if self._scale != 1:
                t = Token.OperandToken('value', 
                    str(self._scale), access, name)
                tokens.append(t)
                
        t = Token.OperandToken('decorator', ']', access, name)
        tokens.append(t)

        return tokens
