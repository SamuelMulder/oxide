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

from collections import defaultdict

"""
{'data': (56600, 3710052983L), 'type': 'seg_off'}
{'data': 4064, 'type': 'rel'}
{'data': 'ebx', 'type': 'reg'}
{'data': {'disp': 0, 'base': 'eax', 'scale': 1, 'idx': None}, 'type': 'eff_addr'}
{'data': 119, 'type': 'imm'}
{'data': 1599043540, 'type': 'off'}
"""

def regs_histo(ops_list):
    histo = defaultdict(int)
    if not ops_list:
        return histo
    for var in ops_list:
        if var:
            if var['type'] == "reg":
                histo[var['data']] += 1
            elif var['type'] == "eff_addr":
                if var['data']['base']:
                    histo[var['data']['base']] += 1
    return histo


