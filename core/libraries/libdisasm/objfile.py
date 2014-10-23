#!/usr/bin/env python2.4

import disasmbuf as DisasmBuf

'''
	libdisasm.objfile

	DisasmBuffer derived classes, largely for convenience
'''

class ObjFile(DisasmBuf.DisasmBuffer):
	# these enums are holdovers from BGO: need fixing
	class TYPE(object):
        	UNK = "unknown"
        	EXEC = "executable"
        	SO = "shared library"
        	AR = "static library"
        	OBJ = "linkable object"
        	DATA = "data"
	class ARCH(object):
        	UNK = "Unknown"
        	X86 = "x86"
        	X8664 = "x86-64"
        	SPARC = "SPARC"
        	PPC = "PPC"
        	ARM = "ARM"
        	JVM = "JVM"
        	CLI = "CLR"
        	IA64 = "IA64"
	class ENDIAN(object):
		LITTLE = "little endian"
		BIG = "big endian"
	class OS(object):
        	UNK = "Unknown"
        	LINUX = "Linux"
        	FREEBSD = "FreeBSD"
        	OPENBSD = "OpenBSD"
        	NETBSD = "NetBSD"
        	SOLARIS = "Solaris"
        	OSX = "OS/X"
        	DOS = "DOS"
        	WIN = "Win16"
        	WIN32 = "Win9x",
        	WINNT = "WinNT/2K/XP"

	def __init__(self, path):
		self._path = path
		try:
			f = file( path, 'rb' )
		except IOError, e:
			sys.stderr.write("Unable to open " + path + str(e))
			raise IOError( e )
		f.seek(0, 2)
		self._size = f.tell()
		f.seek(0, 0)
		try:
			buf = f.read()
			f.close()
		except IOError, e:
			sys.stderr.write("Unable to read " + path + str(e))
			raise IOError( e )
		super(ObjFile, self).__init__(buf)

		self._entry = None
		self._sections = []
		self._symbols = []
		self._strings = []

		self._type = self.TYPE.UNK
		self._arch = self.ARCH.X86
		self._os = self.OS.UNK
		self._endian = self.ENDIAN.LITTLE
		self._addr_size = 4	# Default to 32-bit
	
	def offset_for_rva(self, rva):
		for s in self.sections():
			if rva >= s.rva() and rva < s.rva() + len(s):
				offset = rva - s.rva()
				offset += s.offset()
				return offset
		raise IndexError, 'RVA not contained in file sections'

	def entry(self): return self._entry
	
	def type(self): return self._type
	
	def arch(self): return self._arch

	def endian(self): return self._endian

	def addr_size(self): return self._addr_size
	
	def os(self): return self._os

	def sections(self): return self._sections.__iter__()

	def symbols(self): return self._symbols.__iter__()

	def strings(self): return self._strings.__iter__()

			
class Section(DisasmBuf.DisasmBuffer):
	''' A generic Section class that should be in its own file '''
	class TYPE(object):
	        FILEHDR  = "Header" 	# File format bookeeping info
        	PROGCODE = "Code" 	# Program Executable Code
        	PROGDATA = "Data" 	# Program Readable(/Writeable) Data
        	RESOURCE = "Resource" 	# Resource or embedded UI data
        	SYMBOL = "Symbol" 	# definition of global symbols
        	IMPORT = "Import" 	# def of imported code/data addr
        	EXPORT = "Export" 	# def of exported code/data addr
        	RELOC = "Reloc" 	# Internal addr needing dynamic reloc
        	NOTE = "Note" 		# Advisory info from author/toolchain
	class COMPILER(object):
        	UNK = 'Unknown'
        	GCC = 'gcc'
        	SUN = 'Sun CC'
       		MS = 'Visual C++'
	class LANG(object):
        	ASM = 'Assembler'
        	C = 'C'
        	CPP = 'C++'
        	CSHARP = 'C#'
        	JAVA = 'JAVA'
        	FORTRAN = 'FORTRAN'
	class FLAGS(object):
        	NOINIT = "Unitialized" 	# Uninitialized Data
        	ALLOC = "Allocated" 	# Not allocated
	class ACCESS(object):
        	R  = 0x01
        	W = 0x02
        	X  = 0x04
	def __init__(self, file, name, offset=0, size=0, rva=0,
			 endian='little endian', word_size=1, arch=None):
		self._file = file
		self._name = name
		self._size = size
		self._offset = offset
		slice = file[offset:offset+size]
		super(Section, self).__init__( slice, rva, offset)

		# these might be overridden by section contents
		self._endian = file.endian()
		self._addr_size = file.addr_size()
		self._arch = file.arch()
		self._os = file.os()
		self._word_size = self._addr_size
		self._lang = self.LANG.ASM
		self._compiler = self.COMPILER.UNK

		# these will be changed by caller
		self._type = self.TYPE.FILEHDR
		self._access = 0
		self._flags = []

		# storage
		self._data = []	# data addresses
		#self._symbols = []
		#self._strings = []

	def rva(self): return self._rva

	def offset(self): return self._file_offset

	def name(self): return self._name
	def word_size(self): return self._word_size
	def type(self): return self._type
	def access(self): return self._access
	def lang(self): return self._lang
	def compiler(self): return self._compiler
	def flags(self): return self._flags.__iter__()
	def data(self): return self._data.__iter__()
