#!/usr/bin/env python2.4
import threading

'''
    libdisasm.disasmbuf
    
    Buffer of bytes for disassembly that provides a random-access stream
    interface [i.e. file read(), seek(0, and tell()].

    The primary purpose of a DisasmBuf is to provide a file-like interface
    for the opcode disassembler. The DisasmBuf also provides metainformation
    about the bytes being disassembled, such as their rva or offset, and
    provides method hooks to control the template methods in linear and
    cflow disassembly.
    
    This last bit indicates the class is trying to do too much, and it
    should probably broken up into a buffer, wth users subclassing
    Disassembler to change the method hooks.
'''

class DisasmBuffer(object):
    '''
       Disassembly Buffer
       An immutable sequence of bytes for disassembly, with associated
       RVA and File Offset of the buffer contents, as well as a
       list of instructions disassembled. Maintains a current position
       and supports the functions read(), peek(), seek(), and tell()
       to mimic a read-only file.
        
       Interface:
        read(number_of_bytes)    # read and advance current position
        peek(number_of_bytes)    # read without advancing current position
        seek(position)           # set current position
        tell()                   # return current position
        rva_to_offset(rva)       # return offset for rva
        offset_to_rva(offset)    # return rva for offset
        instructions()           # return iterator over instructions
        instruction(offset)      # return intruction object at offset
        add_insn(insn)           # add instruction for offset to list
        insn_exists(offset)      # does instruction exist for offset?
       Notes:
           * EOF is represented by setting self._pos to None
    '''
    
    class Handle(object):
        '''
            DisasmBuffer handle: equivalent to a File handle.
            Provides a File interface to a DisasmBuffer.
            Note that the disassembler calls DisasmBuffer.handle() to
            obtain this object.
        '''
        def __init__(self, buf, rva_func, offset=0):
            # current position
            self._pos = offset
            self._bytes = buf
            self._offset_to_rva = rva_func
            
        # Immutable sequence interface: forwarded to byte string
        # OK his is duplicated with DisasmBuffer, but it is convenient
        # to have the interface available in each.
        def __len__(self):
            return len(self._bytes)

        def __iter__(self):
            return iter(self._bytes)

        def __contains__(self, item):
            return item in self._bytes

        def __getitem__(self, key):
            return self._bytes.__getitem__(key)

        def __setitem__(self, key, value):
            raise TypeError, "DisasmBuf handle is immutable"

        def __delitem__(self, key):
            raise TypeError, "DisasmBuf handle is immutable"

        # File interface
        def read(self, num=1):
            ''' Read num bytes from buffer '''
            if self._pos is None:
                raise EOFError
        
            pos = self._pos + num
            if (pos) > len(self._bytes):
                raise IndexError, "%d + %d exceeds buffer length %d" %\
                    (self._pos, num, len(self._bytes))

            buf = self._bytes[self._pos:pos]
        
            if pos == len(self._bytes):
                self._pos = None    # EOF
            else:
                self._pos = pos

            return buf

        def peek(self, num=1):
            ''' Read num bytes without advancing buffer pos '''
            if self._pos is None:
                raise EOFError
            
            if self._pos + num > len(self._bytes):
                raise IndexError, "%d + %d exceeds buffer length %d" %\
                    (self._pos, num, len(self._bytes))
            buf = self._bytes[self._pos:self._pos + num]
            return buf

        def seek(self, offset):
            ''' Set current position in buffer '''
            if offset > len(self._bytes):
                raise IndexError, "%d exceeds buffer length %d"  % \
                    (offset, len(self._bytes))
            elif offset == len(self._bytes):
                self._pos = None    # EOF
            else:
                self._pos = offset

        def tell(self):
            ''' Return current position in buffer ''' 
            ''' NOTE: when current position is EOF, this returns
                      the entire length of the buffer rather than 
                      EOF. This makes it possible to do:
                          start_offset = h.tell()
                          ... # misc reads
                          size = h.tell() - start_offset 
            '''
            if self._pos is None:
                return len(self._bytes)
            return self._pos

        def tell_rva(self):
            ''' Return rva for current position in buffer '''
            ''' See NOTE for tell() method '''
            if self._pos is None:
                return self._offset_to_rva(len(self._bytes))
            return self._offset_to_rva(self._pos)
            
    def __init__(self, bytes, rva=0, file_offset=0):
        # string of bytes to disassemble
        self._bytes = bytes
        self._rva = rva
        self._file_offset = file_offset
        # instructions disassembled, keyed by offset
        self._instructions = {}
        self._instruction_lock = threading.Lock()
        
    def handle(self, offset=0):
        return DisasmBuffer.Handle(self._bytes, self.offset_to_rva, offset)

    # Immutable sequence interface: forwarded to byte string
    def __len__(self):
        return len(self._bytes)

    def __iter__(self):
        return iter(self._bytes)

    def __contains__(self, item):
        return item in self._bytes

    def __getitem__(self, key):
        return self._bytes.__getitem__(key)

    def __setitem__(self, key, value):
        raise TypeError, "DisasmBuf sequence is immutable"

    def __delitem__(self, key):
        raise TypeError, "DisasmBuf sequence is immutable"

    
    # Disassembly buffer interface
    def rva_to_offset(self, rva):
        ''' Calculate Offset for RVA '''
        offset = rva - self._rva
        if offset < 0 or offset > len(self._bytes):
            raise IndexError, "%d exceeds buffer length %d"  % \
                (offset, len(self._bytes))
        return offset
    
    def offset_to_rva(self, offset):
        ''' Calculate RVA for Offset '''
        if offset < 0 or offset > len(self._bytes):
            raise IndexError, "%d exceeds buffer length %d"  % \
                (offset, len(self._bytes))
        return self._rva + offset
    
    
    def instructions(self):
        ''' Return a (key, value) iterator over the instructions.
            'key' is instruction offset in buffer, 'value' is instruction
        '''
        self._instruction_lock.acquire()
        iter = self._instructions.iteritems()
        self._instruction_lock.release()
        return iter
        # TODO: replace with generator over sorted keys
        #return self._instructions.itervalues()

    def instruction(self, offset):
        ''' Return the instruction at offset '''
        self._instruction_lock.acquire()
        insn = self._instructions.get(offset, None)
        self._instruction_lock.release()
        return insn

    def add_insn(self, insn):
        '''
            Adds an insn to the list of instructions already 
            disassembled.
        '''
        self._instruction_lock.acquire()
        self._instructions[insn.offset()] = insn
        self._instruction_lock.release()
    
    def exists(self, offset):
        '''
            Instruction exists for offset?
            Determines whether to disassemble the given offset.
            By default, if an instruction already exists for
            an offset in the buffer, that offset is not disassembled
            again. This prevents loops during cflow disasm.
            Override this method to overwrite instructions that
            have already been disassembled.
        '''
        self._instruction_lock.acquire()
        result = offset in self._instructions
        self._instruction_lock.release()
        return result
