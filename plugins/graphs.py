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

import api, sys_utils
import os
import networkx as nx
from collections import defaultdict

def graph_stats(args, opts):
    """ Plugin: Prints a set of statistics about the call and control flow graphs
        Syntax: graph_stats <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    args = api.expand_oids(valid)

    for o in args:
        cg = api.get_field("call_graph", o, "graph")
        if not cg: continue
        size = len(cg.nodes())
        in_histo = build_freq_histo(cg.in_degree())
        out_histo = build_freq_histo(cg.out_degree())
        cfgs = api.retrieve("cfg", o)
        size_dict = { i : cfgs[i].size() for i in cfgs if cfgs[i] }
        size_histo = build_freq_histo(size_dict)
        bbs = 0
        for s in size_histo:
            bbs += s * size_histo[s]
        name = api.get_field("file_meta", o, "names").pop()
        print "-----------------"
        print " Graph stats for ", name
        print 
        print " Functions = ", size
        print " Basic Blocks = ", bbs
        print " Call graph in-degree: " 
        pretty_print_dicts(in_histo)
        print " Call graph out-degree: " 
        pretty_print_dicts(out_histo)
        print " CFG sizes: " 
        pretty_print_dicts(size_histo)
    return []
    
def write_graph(args, opts):
    """ Plugin: Writes out the adjacency list for the graph of a file to oid.adj_list
                in the scratch directory
        Syntax: write_graph <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    args = api.expand_oids(valid)

    for o in args:
        cg = api.retrieve("call_graph", o)
        if not cg:
            continue
        else:
            cg = cg['graph']
        cfgs = api.retrieve("cfg", o)
        call_map = api.retrieve("map_calls", o)
        sys_calls = call_map['system_calls']
        bbs = api.retrieve("basic_blocks", o)
        header = api.get_field("object_header", o, "header")
        fpath = os.path.join(api.scratch_dir, o + ".adj_list")
        print "Writing graph file to %s" % (fpath)
        fd = file(fpath, 'wb')
        fd.write("Functions: " + str(cg.number_of_nodes()) + "\n")
        num_bbs = 0
        for bb in bbs:
            num_bbs += len(bbs[bb])
        fd.write("Basic blocks: " + str(num_bbs) + "\n\n")
        
        for n in cg.nodes():
            edges = cg.successors(n)
            s = len(edges)
            outstr = str(n) + " " + str(s) + " "
            for e in edges:
                outstr += str(e) + " "
            fd.write(outstr + "\n")
        fd.write("\n--------------------------------------------\n")
        for cfg in cfgs:
            if not cfgs[cfg]: continue
            fd.write(str(cfg) + "\n")
            for n in cfgs[cfg].nodes():
                edges = cfgs[cfg].successors(n)
                s = len(edges)
                outstr = str(n) + " " + str(s) + " "
                for e in edges:
                    outstr += str(e) + " "
                fd.write(outstr + "\n")
            fd.write("\n--------------------------------------------\n")
        funcs = bbs.keys()
        funcs.sort()    
        fd.write("SYSTEM CALLS \n\n")
        for s in sys_calls:
            rva = header.get_rva(s)
            prev = None
            for f in funcs:  # find which function the system call is in
                if f > rva: break
                else: prev = f 
            if not prev: continue
            func = bbs[prev]
            for bb in func:  # find which basic block the system call is in
                if bb['first_insn'] <= rva and bb['last_insn'] >= rva:
                    fd.write(str(bb['first_insn']) + " " + sys_calls[s] + "\n")
                    break 
                
        fd.close()
    
exports = [graph_stats, write_graph]

############ UTILITIES #############################

def build_freq_histo(d):
    h = defaultdict(int)
    for i in d:
        h[d[i]] = h[d[i]] + 1
    return h    
    
def pretty_print_dicts(d):
    keys = d.keys()
    keys.sort()
    for k in keys:
        print k, ":", d[k], ", ",
    print