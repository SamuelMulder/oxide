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

"""Plugin: A set of functions to analyze the data within string buffers
"""
import base64, hashlib, zlib 
from itertools import izip, cycle


def ascii(args, opts):
    """ 
        Plugin: Prints and passes the decimal ascii value of a string
        Syntax: ascii <string>
    """
    s = flatten_list_to_string(args)
    args = [ord(str(i)) for i in s]
    args_s = " ".join([str(i) for i in args])
    print " - ASCII:%s is %s" % (repr(s), repr(args_s))
    print
    return args

def hexval(args, opts):
    """ 
        Plugin: Prints and passes the hex value of the ASCII decimal value a string
        Syntax: hexval <string>
    """
    s = flatten_list_to_string(args)
    a = ascii(s, None) # Get the ASCII ordinal characters first
    args = [ hex(i) for i in a ]
    s = " ".join([str(i) for i in a])
    hex_s = " ".join([str(i) for i in args])
    print " - Hex:%s is %s" % (repr(s), repr(hex_s))
    print
    return args

def encode64(args, opts):
    """ 
        Plugin: Prints and passes the base64 encoding of a string
        Syntax: encode64 <string>
    """
    s = flatten_list_to_string(args)
    try:
        args = base64.encodestring(s).strip()
    except:
        raise ShellRuntimeError("%s cannot be base64 encoded" % s)
    print " - Base 64 encode:%s to %s" % (repr(s), repr(args))
    print
    return args

def decode64(args, opts):
    """ 
        Plugin: Prints and passes the base64 decoding of a string
        Syntax: decode64 <string>
    """
    s = flatten_list_to_string(args)
    try:
        args = base64.decodestring(s).strip()
    except:
        raise ShellRuntimeError("%s is an invalid base64 string" % s)
    print " - Base 64 decode:%s to %s" % (repr(s), repr(args))
    print
    return args
    
    
def md5(args, opts):
    """ 
        Plugin: Prints and passes the md5 of a string
        Syntax: md5 <string>
    """
    s = flatten_list_to_string(args)
    args = hashlib.md5(s).hexdigest() 
    print " - MD5:%s is %s " % (repr(s), repr(args))
    print
    return args


def sha1(args, opts):
    """ 
        Plugin: Prints and passes the sha1 of a string
        Syntax: sha1 <string>
    """
    s = flatten_list_to_string(args)
    args = hashlib.sha1(s).hexdigest() 
    print " - SHA1:%s is %s " % (repr(s), repr(args))
    print
    return args
    
    
def sha256(args, opts):
    """ 
        Plugin: Prints and passes the sha256 of a string
        Syntax: sha256 <string>
    """
    s = flatten_list_to_string(args)
    args = hashlib.sha256(s).hexdigest() 
    print " - SHA256:%s is %s " % (repr(s), repr(args))
    print
    return args
    
    
def xor(args, opts):
    """ 
        Plugin: Prints and passes the output of xoring a string with the passed key
        Syntax: xor <string> --key<xor_key>
    """
    if not "key" in opts:
        raise ShellSyntaxError("Need to specify a key. --key=<xor_key>")
    xor_key = opts["key"] 
    xor_key = flatten_list_to_string(xor_key)
    s = flatten_list_to_string(args)
    args = ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(s, cycle(xor_key)))
    print " - XOR with key:%s of %s is %s" %(repr(xor_key), repr(s), repr(args))
    print
    return args

def compress(args, opts):
    """ 
        Prints: Converts a list to a string and passes the zlib compressed value of that string
        Syntax: compress string
    """
    s = flatten_list_to_string(args)
    args = zlib.compress(s)
    print " - Compressed %s is %s" % (repr(s), repr(args))
    print
    return args
    
    
def decompress(args, opts):
    """ 
        Prints: Converts a list to a string and passes the zlib decompressed value of that string
        Syntax: compress string
    """
    s = flatten_list_to_string(args)
    args = zlib.decompress(s)
    print " - Decompressed %s is %s" % (repr(s), repr(args))
    print
    return args
        
        
exports = [ascii, encode64, decode64, md5, sha1, sha256, xor, hexval, 
           compress, decompress]

####### UTILITIES ##############################################################
def flatten_list_to_string(l):
    """ Given a list of items return a string where all of the items are
        cast to a string and comcatinated together and spaces are inserted
        between each item.
        [ 1, "Abc", 3.4 ] -> "1 Abc 3.4"
    """
    if isinstance(l, str):
        return l
        
    s = ""
    for i in l:
        if isinstance(i, list):
            return flatten_list_to_string(i)
        else:
            s += " " +str(i)
    return s.strip()
    
    
def string_to_int(s):
    if not isinstance(s, str):
        return s
    try:
        return int(eval(s))
    except (ValueError, NameError):
        return s
            
            
            
            
            
            
            
            
            