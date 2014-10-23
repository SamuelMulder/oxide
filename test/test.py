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

import os, sys, shutil, string, logging, optparse, unittest, _path_magic
import core.oxide as oxide
from sys_utils_test import sys_utils_test
from core_test import core_test
from module_test import module_test
from shell_test import shell_test
 
parser = optparse.OptionParser()
parser.add_option("-c", "--core", action="store_true", dest="core",
                    help="Run the core tests")

parser.add_option("-a", "--all", action="store_true", dest="all",
                    help="Run all of the tests")

parser.add_option("-i", "--interactive", action="store_true", dest="interactive",
                    help="Run interactive tests")

parser.add_option("-v", "--verbose", action="count", dest="verbose",
                    help="Verbose test output")
                    
parser.add_option("-m", "--modules", action="store_true", dest="modules",
                    help="Run module tests")
                    
parser.add_option("-o", "--onemodule", action="store", dest="onemodule",
                    help="Test single module")

parser.add_option("-s", "--shell", action="store_true", dest="shell",
                    help="Test the shell")
                    
(options, args) = parser.parse_args()


        
if __name__ == "__main__":
    if options.all or (not options.core and not options.modules 
        and not options.onemodule and not options.shell):
        options.core = True
        options.modules = True
        options.shell = True     
   
    if options.onemodule:
        print "Testing the " + options.onemodule + " module"
        module_test(singlemodule=options.onemodule)
        
    if options.modules:
        print "Running module tests."
        module_test()
    else:
        print "Skipping module tests."
        
    if options.core:
        print "Running sys_utils tests."
        suite = unittest.TestLoader().loadTestsFromTestCase(sys_utils_test)
        unittest.TextTestRunner().run(suite)
        
        print "Running core tests."
        suite = unittest.TestLoader().loadTestsFromTestCase(core_test)
        unittest.TextTestRunner(verbosity=options.verbose).run(suite)
    else:
        print "Skipping core tests." 
    
    if options.shell:
        print "Running shell tests."
        suite = unittest.TestLoader().loadTestsFromTestCase(shell_test)
        unittest.TextTestRunner(verbosity=options.verbose).run(suite)        

    
