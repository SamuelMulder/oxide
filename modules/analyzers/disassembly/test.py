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

import unittest
import os

# This file needs to be named test.py and reside in the same folder as the module itself.
# Class name must be <modulename>_test and must inherit from unittest.TestCase
# Function names must start with test_

class disassembly_test(unittest.TestCase):
    def test_disassembly(self):
        sample_files = os.listdir(self.oxide.config.dir_sample_dataset)
        oid_list = []
        for sample_file in sample_files:
            fp = os.path.join(self.oxide.config.dir_sample_dataset, sample_file)
            oid, newfile = self.oxide.import_file(fp)
            if not oid: continue
            oid_list.append(oid)
        for oid in oid_list:
            src_type = self.oxide.get_field("src_type", oid, "type") 
            if src_type == 'PE' or src_type == 'ELF' or src_type == 'MACHO':
                self.assertTrue(self.oxide.process("disassembly", [oid], {}), 
                                "disassembly not able to process a PE, ELF, or MACHO file")
            else:
                self.assertFalse(self.oxide.process("disassembly", [oid], {}), 
                                 "disassembly able to process a not-PE/ELF/MACHO file")
