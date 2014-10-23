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

import os, sys
import _path_magic

def remove_empty_dirs(directory):
    directories = set()
    print "  Removing empty directories in and below the directory", directory
    for (path, dirs, files) in os.walk(directory):
        for d in dirs:
            fullpath = os.path.join(path, d)
            if len(os.listdir(fullpath)) == 0:
                os.removedirs(fullpath)	
                directories.add(fullpath)
    #print "  %s directories were removed." % len(d)
    if directories:
        print "  The following directories were removed:"
        for i in directories:
            print " ", i
    else:
        print "  No empty directories found"
        

if __name__ == "__main__":
    if len(sys.argv) != 2:
        d = d = _path_magic.oxide_dir
    else:
        d = sys.argv[1]
        d = os.path.abspath(d)
        
    if not os.path.isdir(d):
        print "  %s directory does not exist." % d
        exit()

    remove_empty_dirs(d)
