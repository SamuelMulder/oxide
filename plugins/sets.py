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

import api, shell_api, progress 

def union(args, opts):
    """ Plugin: union
        Syntax: union @x @y | show 
        
        Returns the union of set types x and y.  Lists, dictionaries, etc get converted
        to sets so this works with the results of things like opcode_ngrams.
    """    
    set_args = []
    final = set()
    for a in args:
        if isinstance(a, str):
            final.add(a)
        else:
            try:
                set_args.append(set(a))
            except:
                continue
    for a in set_args:
        final.update(a)
        
    return [final]
    
def intersect(args, opts):
    """ Plugin: intersect
        Syntax: intersect @x @y | show 
        
        Returns the intersection of set types x and y.  Lists, dictionaries, etc get converted
        to sets so this works with the results of things like opcode_ngrams.
    """    
    set_args = []
    final = set()
    for a in args:
        try:
            set_args.append(set(a))
        except:
            continue
    final = set_args.pop()
    for a in set_args:
        final = final.intersection(a)
        
    return [final]
    
def unique(args, opts):
    """ Plugin: unique
        Syntax: unique @x @y | show 
        
        Returns the elements in set type x that do not exist in set type y.  Lists, 
        dictionaries, etc get converted to sets so this works with the results of 
        things like opcode_ngrams.
    """    
    set_args = []
    final = set(args[0])
    for a in args[1:]:
        try:
            set_args.append(set(a))
        except:
            continue
    for a in set_args:
        final = final.difference(a)
        
    return [final]
    
    
exports = [union, intersect, unique]
