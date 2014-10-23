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

import api
from networkx import DiGraph

def match_instr_cfg(args, opts):
    """ Plugin: Attaches the instructions associated with the control flow returned by the cfg module
        Syntax:
                match_instr_cfg %<oid>
    """
    args, invalid = api.valid_oids(args)
    args = api.expand_oids(args)
    if not args:
        raise ShellSyntaxError("Must provide an oid")
    for oid in args:
        features = api.retrieve('asm_semantics', [oid])               
        asm = api.retrieve('function_extract', [oid])
        cfg = api.retrieve('cfg', [oid])
        basic_blocks = api.retrieve('basic_blocks', [oid])
        for func_address in sorted(cfg.keys()):
            if cfg[func_address]:
                for node in sorted(cfg[func_address]):
                    line_num = (i for i in xrange(len(basic_blocks[func_address])) if basic_blocks[func_address][i]['first_insn'] == node).next()
                    num_insns = basic_blocks[func_address][line_num]['num_insns']
                    line_num = (i for i in xrange(len(asm[func_address]['insns'])) if asm[func_address]['insns'][i]['addr'] == node).next()
                    insns_set = asm[func_address]['insns'][line_num:line_num+num_insns]
                    cfg[func_address][node]['insns'] = insns_set
        return cfg
exports = [match_instr_cfg]

