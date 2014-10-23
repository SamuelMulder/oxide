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
from glob import glob
import _path_magic
import core.config as config

def remove_locks(directory):
    print "  Removing lock files from the directory", directory
    lock_files = glob(os.path.join(d, "*.lock.*"))
    lock_files.extend(glob(os.path.join(d, "TMP*")))
    if lock_files:
        print "  Removing locks files:"
    for f in lock_files:
        print " ",f
        os.remove(f)	
    print "  %s lock file(s) were removed." % len(lock_files)
	

if __name__ == "__main__":
    if len(sys.argv) != 2:
        d = config.dir_datastore
    else:
        d = sys.argv[1]
        d = os.path.abspath(d)
    if not os.path.isdir(d):
        print "  %s directory does not exist." % d
        exit()

    remove_locks(d)
