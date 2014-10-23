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

desc = 'This module should be used by higher level modules that want to get disassembly.'
name = 'disassembly'

import api
import logging

logger = logging.getLogger(name)
logger.debug('init')

choices = ['linear_intel_disassembler']
opts_doc = {'module': {'type': str, 'mangle': False, 'default': 'auto', 
            'valid': choices}}

def documentation():
    return {'description': desc, 'opts_doc': opts_doc, 'set': False, 'atomic': True}

def results(oid_list, opts):
    logger.debug('results()')
    disassembler = choose_disassembler(opts)
    if disassembler not in choices:
        logger.warn('disassembly only accepts (%r)' % choices)
        return None

    try:
        disasm = api.retrieve(disassembler, oid_list[0], opts)

    except Exception, msg:
        logger.error("disassembly failed for %s: %s", oid_list[0], msg)
        return None

    return disasm

def choose_disassembler(opts):
    """
    Returns the best disassembler available. This can be called only after all
    the modules have been loaded

    default/auto disassembler is linear_intel_disassember (32-bit only)
    """
    dis_tool = 'linear_intel_disassembler'

    logger.debug('using disassembler (%s)', dis_tool)
    return dis_tool
