"""
Copyright (c) 2014 Sandia Corporation. 
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation, 
the U.S. Government retains certain rights in this software.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import struct

def isPE(stream):
	return stream[:2] == "MZ"
	
def isZM(stream):
    return stream[:2] == "ZM"

def isPE32(stream):
    sig = struct.unpack("BBBB", pe32[60:64])[0]
    op_header = sig + 24
    return isPE(stream) and op_header == "\x0b\x01"

def isPEPlus(stream):
    sig = struct.unpack("BBBB", pe32[60:64])[0]
    op_header = sig + 24
    return isPE(stream) and op_header == "\x0b\x02"

def isELF(stream):
    return stream[:4] == "\x7fELF"

def isELF32(stream):
    return isELF(stream) and stream[5] == "\x01"

def isELF64(stream):
    return isELF(stream) and stream[5] == "\x02"

def isELF32_intel(stream):
    return isELF32(stream) and stream[18] == "\x03"

def isELF32_arm(stream):
    return isELF32(stream) and stream[18] == "\x40"


def isScript(stream):
    return stream[:2] == "#!"

def isPDF(stream):
    return stream[:4] == "%PDF"

def isGIF(stream):
    return stream[:4] == "GIF8"

def isJPG(stream):
    return stream[:2] == "\xFF\xD8"
        
def isPNG(stream):
    return stream[:8] == "\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"

def isBMP(stream):
    return stream[:2] == "BM"
    
def isTIFF(stream):
    return stream[:4] == "\x49\x49\x2A\x00" or stream[:4] == "\x4D\x4D\x00\x2A"

def isPS(stream):
    return stream[:2] == "%!"
    
def isMP4(stream):
    return stream[:12] == "\x00\x00\x00\x14ftyp3gp5" or \
            stream[:12] == "\x00\x00\x00\x14ftypisom" or \
            stream[:12] == "\x00\x00\x00\x20ftyp3gp5" or \
            stream[:12] == "\x00\x00\x00\x20ftypisom" 

def isM4A(stream):
    return stream[:12] == "\x00\x00\x00\x20ftypM4A\x20"

def isZIP(stream):
    return stream[:4] == "PK\x03\x04"
    
def isCompress(stream):
    return stream[:2] == "\x1f\x9d"

def isBZ2(stream):
    return stream[:2] == "BZ"

def isGZip(stream):
    return stream[:2] == "\x1f\x8b"
    
def isFITS(stream):
    return stream[:6] == "SIMPLE"
    
def isTAR(stream):
    return len(stream) > 265 and stream[257:257+5] == "ustar"
    
def isCAB(stream):
    return stream[:4] == "MSCF"
        
def isMSOffice(stream):
    return stream[:8] == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    
def isJava(stream):
    return stream[:8] == "\xCA\xFE\xD0\x0D"

def isVmem(stream):
    return stream[:6] == "\x53\xff\x00\xf0\x53\xff"

def isXML(stream):
    return stream[:5] == "<?xml" or stream[:5] == "<?XML"
        
def isMachO(stream):
    return stream[:4] == "\xce\xfa\xed\xfe" or stream[:4] == "\xfe\xed\xfa\xce" or \
        stream[:4] == "\xcf\xfa\xed\xfe"

def isDEX(stream):
    return stream[:4] == "dex\n"
    
def isFatBinary(stream):
    return stream[:4] == "\xca\xfe\xba\xbe"

def file_type(stream):
    if isPE(stream):
        type = "PE"
    elif isZM(stream):
        type = "ZM"
    elif isELF(stream):
        type = "ELF"
    elif isScript(stream):
        type = "Script"
    elif isPDF(stream):
        type = "PDF"
    elif isGIF(stream):
        type = "GIF"
    elif isJPG(stream):
        type = "JPG"
    elif isPNG(stream):
        type = "PNG"
    elif isBMP(stream):
        type = "BMP"
    elif isTIFF(stream):
        type = "TIFF"
    elif isPS(stream):
        type = "PS"
    elif isMP4(stream):
        type = "MP4"
    elif isM4A(stream):
        type = "M4A"
    elif isZIP(stream):
        type = "ZIP"
    elif isCompress(stream):
        type = "Compress"
    elif isBZ2(stream):
        type = "BZ2"
    elif isGZip(stream):
        type = "GZIP"
    elif isFITS(stream):
        type = "FITS"
    elif isTAR(stream):
        type = "TAR"
    elif isCAB(stream):
        type = "Microsoft CAB File"
    elif isMSOffice(stream):
        type = "Microsoft Office File"
    elif isJava(stream):
        type = "JAVA Bytecode"
    elif isVmem(stream):
        type = "VMEM"
    elif isXML(stream):
        type = "XML"
    elif isMachO(stream):
        type = "MACHO"
    elif isDEX(stream):
        type = "DEX"
    elif isFatBinary(stream):
        type = "OSX Universal Binary"
    else:
        type = "Unknown"
    return type
    
