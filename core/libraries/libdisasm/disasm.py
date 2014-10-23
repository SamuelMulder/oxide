#!/usr/bin/env python2.4
'''
    libdisasm.disasm
    The main disassembler class.
    
    Disassembly is implemented with the disassemble() method,
    which uses the following strategies:
        single : disassemble a single instruction
        linear : disassemble a buffer sequentially
        cflow  : disassemble a buffer, following control flow
    Additional strategies can be added to Disassembler.strategies
    or supported in a subclass.
    
    The 'linear' and 'cflow' strategies use template methods to
    determne whether to continue disassembly, to process the instruction,
    and to resolve the targets of jump and call instructions. These
    can be replaced in subclasses.
'''
import threading
import exception as Excep
import instruction as Insn


class Disassembler(object):
    '''
       libdisasm.disasm.Disassembler
       Disassemble the contents of a DisasmBuffer.
       This is a base class, and while not actually abstract,
       it is not intended to be called directly. The behavior
       of the base class is to disassemble starting at given offset
       (or 0) in the DisasmBuffer. Disassembly halts with an
       EOFError when the end of the DisasmBuffer is reached.
    '''
    class DisassemblerOptions(object):
        _supported_isa = ('ia32', 'ia16')

        _defaults = { 
                 # ISA to use for disassembly
                 'isa' : 'ia32', 
                 # Do not disasm sequences of null_limit NULL bytes
                 'null_limit' : 0,
                 # overwrite existing instructions in buffer
                 'overwrite' : False,     
                 # Wildcard byte used in signatures
                 'sig_wildcard' : 0xF4
               }

        def __init__(self, dict=None):
            self._opts = self._defaults.copy()
            if dict:
                self.set_options(dict)

        def supported_isa(self):
            ''' Return a list of the supported ISAs '''
            return self._supported_isa.list()

        def supported_options(self):
            ''' Return a list of the supported options '''
            return self._defaults.keys()

        def default_options(self):
            return self._defaults.copy()

        def set_options(self, dict):
            self._opts.update(dict)
        
        def get_option(self, name):
            return self._opts.get(name, self._defaults[name])
        
        def get_options(self):
            return self._opts.copy()

    def __init__(self, options=None):
        self._options = Disassembler.DisassemblerOptions(options)
        self.dis = self.disasm_factory(self._options.get_option('isa'))
    
    def disasm_factory(self, isa):
        ''' Instantiate an architecture-specific disassembler. '''
        if self._options.get_option('isa') == 'isa16':
             # 16-bit legacy mode is just 32-bit mode with an
            # address size of 2.
            import ia32.disasm as ia32
            return ia32.OpcodeDisassembler(addr_size=2)
        
        elif self._options.get_option('isa') == 'x86_64':
            raise NotImplementedError, 'X86-64 not supported'
            import libdisasm.x86_64.disasm as x86_64
            self._dis = x86_64.OpcodeDisassembler()
            
        else:
            # default to IA32
            import ia32.disasm as ia32
            return ia32.OpcodeDisassembler()

    # TODO: more like this for endianness, word size, etc
    def max_insn_length(self):
        return self.dis.max_insn_length()

    def disassemble(self, buf, offset=0, rva=None):
        '''
           Disassemble the contents of a DisasmBuf while self.cont()
           returns True. Invokes self.process() on each instruction
           disassembled.
        '''
        try:
            callable(buf.handle)
            callable(buf.instructions)
        except AttributeError, e:
            raise TypeError, 'disassemble() requires a DisasmBuffer object'

        if rva is not None: 
            offset = buf.rva_to_offset(rva)
        
        handle = buf.handle(offset)

        while 1:
            if buf.exists(offset) and not self.overwrite():
                offset += buf.instruction(offset).size()
                handle.seek(offset)
                continue
            
            try:
                insn = self.dis.disassemble(handle, self._options)
            except Excep.DecodeError, e:
                # generate invalid instruction and keep going
                insn = Insn.InvalidInstruction( offset,
                        buf.offset_to_rva(offset), buf[offset] )
            self.process(buf, insn)
            offset += insn.size()

            if not self.cont(buf, handle, insn):
                break
            
        return buf.instructions()

    def overwrite(self):
        ''' Return boolean: Overwrite existing instructions in buffer? '''
        return self._options.get_option('overwrite')
    
    def options(self):
        return self._options
    
    # Template methods: override these to change behavior
    def process(self, buf, insn):
        '''
            Process disassembled instruction.
            Adds an insn to the list of instructions already 
            disassembled. Override this method in a subclass to 
            perform additional processing of insn.
        '''
        buf.add_insn(insn)
        
    def cont(self, buf, handle, insn):
        '''
            Continue disassembly?
            Override this in a subclass to disassemble a range of 
            bytes or to force disassembly to abort on a given condition 
            (e.g. once a pattern of instructions have been found).
            The parameters allow any state of DisasmBuffer, 
            DisasmBuffer.Handle, or Instruction to determine whether
            disassembly continues.
        '''
        return True
        
class SingleDisassembler(Disassembler):
    '''
       libdisasm.Disassemble.SingleDisassembler
       Disassemble a single instruction in a DisasmBuffer.
    '''
    def cont(self, buf, handle, insn):
        '''
            Continue disassembly? Always false for single insn disassembly.
        '''
        return False

class LinearDisassembler(Disassembler):
    '''
       libdisasm.Disassemble.LinearDisassembler
       Disassemble the contents, or a subset of the contents,
       of a DisasmBuffer.
    '''
    def disassemble(self, buf, offset=0, rva=None, length=0):
        if length:
            self._length = length
        else:
            self._length = len(buf) - offset - 1

        super(LinearDisassembler, self).disassemble(buf, offset, rva)
        
    def cont(self, buf, handle, insn):
        ''' Continue disassembly? '''
        if handle.tell() >= self._length:
            return False
        return True

    
class ControlFlowDisassembler(Disassembler):
    '''
        libdisasm.disasm.ControlFlowDisassembler
        Disassemble the contents of a DisasmBuffer, recursing to
        follow all branches and calls. Disassembly of each
        recursion ends when a JMP or RET instruction is encountered,
        or when the end of the buffer is reached.
    '''
    def cont(self, buf, handle, insn):
        ''' Continue disassembly? '''
        end_insns = ('jmp', 'ret', 'tret')
        if insn.type() in end_insns:
            return False
        if handle.tell() is None:
            return False
        return True

    def _is_cflow_insn(self, insn):
        branch_insns = ('jmp', 'jcc', 'call', 'callcc')
        return insn.type() in branch_insns

    def cflow_recurse(self, buf, offset):
        ''' Recurse calling disassemble on offset.
            This is a template method that can be can be overridden 
            in multithreaded disassemblers.
        '''
        if buf.exists(offset) and not self.overwrite():
            return
        self.dissemble(buf, offset)

    def process(self, buf, insn):
        ''' Process disassembled instruction. '''        
        super(ControlFlowDisassembler, self).process(buf, insn)
        
        # could also test for executable operands
        if self._is_cflow_insn(insn):
            dest = self.resolve(insn.operand(0))
            if dest:
                self.cflow_recurse(buf, dest)

    def resolve(self, operand):
        '''
           Resolve operand.
           Called during cflow disassembly to get the target of
           a branch or call. Returns an offset in DisasmBuf
           or None if the operand could not be resolved or
           lies outside of buffer. Override this in a subclass
           to emulate the stack, track register contents, create
           cross references, or schedule future disassembly of
           an address outside of this DisasmBuf.
        '''

        type = operand.type()
        if "relative" in type:
            return operand.offset()
        elif type == "immediate" or type == "offset":
            return operand.value.unsigned()
            
        # "segment:offset" not used in cflow opcodes
        # "register" must be emulated
        # "effective address" must be emulated
        # ...will need self.rva_to_offset() for more these as well.
            
        return None


class DisassemblerThread(threading.Thread):
        def __init__(self, disassembler, handle, offset):
            super(DisassemblerThread, self).__init__()
            self._disassembler = disassembler
            self._disasm_handle = handle
            self._disasm_offset = offset
            
        def run(self):
            self._disassembler.disassemble(self._disasm_handle, 
                                           self._disasm_offset)


class ControlFlowThreadedDisassembler(ControlFlowDisassembler):
    '''
        libdisasm.disasm.ControlFlowThreadedDisassembler
        Multithreaded version of ControlFlowDisassembler
        
        NOTE : Running this on anything but simple code is probably
        a very BAD idea. There are currently no limits on how many
        threads are created.
        TODO: introduce a thread pool.
    '''
    def __init__(self, options=None):
        super(ControlFlowThreadedDisassembler, self).__init__(options)
        self._threads = []

    def disassemble(self, buf, offset=0, rva=None, length=0):
        result = super(ControlFlowThreadedDisassembler, self).disassemble(
                        buf, offset, rva)
        for t in self._threads:
            t.join()
        
        return result
    
    def cflow_recurse(self, buf, offset):
        # TODO: find a more efficient way to manage the threads
        if buf.exists(offset) and not self.overwrite():
            return
        dis = ControlFlowThreadedDisassembler(self.options().get_options())
        t = DisassemblerThread(dis, buf, offset)
        t.start()
        self._threads.append(t)
 
 
# Convenience function to call the correct disassembler based on a
# user-specified strategy. The list of strategies can be modified by an 
# application. This isn't entirely useful.
strategies = { 'single': SingleDisassembler, 
               'cflow': ControlFlowDisassembler,
               'cflow-mt': ControlFlowThreadedDisassembler, 
               'linear': LinearDisassembler }
               
def disassemble(strategy, buf, offset=None, length=None):
    '''
       Disassemble contents of a DisasmBuffer.
        strategy = single (disasm single instruction), 
                   cflow (disasm following targets of jumps and calls), 
                  linear (disasm all bytes from'offset' to end of buffer.
        buf = a Disasmbuf or a string of bytes. If a string, a DisasmBuf 
              will be created.
        offset = offset into buffer to disassemble
        length = number of bytes to disassemble, if supported by the strategy.
    '''
    try:
        buf.peek()
    except AttributeError, e:
        buf = DisasmBuffer(buf)
        
    try:
        dis = strategies[strategy]
    except KeyError, e:
        raise UserWarning, \
              'Nonexistent disassembler strategy ' + strategy
    if length:
        
        return dis(buf, offset, length=length)

    return dis(buf, offset)
