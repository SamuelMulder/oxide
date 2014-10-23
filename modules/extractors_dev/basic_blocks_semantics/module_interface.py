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

desc = 'This module builds a dictionary of semantic properties within basic blocks.'
name = 'basic_blocks_semantics'

import api
import logging
import re

logger = logging.getLogger(name)
logger.debug('init')

opts_doc = {}
callTypes = {}
callTypes['exception_handling'] = ['raiseexception', '_cxxthrowexception', '__cxa_allocate_exception', '__cxa_end_catch', '__cxa_get_exception_ptr', '__cxa_throw', '__cxa_begin_catch', 'setlasterror', 'getlasterror']
callTypes['printer'] = ['startdocprintera', 'startpageprinter', 'enddocprinter', 'closeprinter', 'writeprinter', 'endpageprinter', 'enumprintersa', 'openprintera']
callTypes['fileIO'] = ['createfila', 'deltefilea', 'readfile', 'writefile', 'flushfilebuffers']
callTypes['registry_access'] = ['regopenkeya', 'regqueryvalueexa', 'regclosekey', 'regcreatekeya', 'regsetvalueexa', 'regdeletekeya', 'regenumkeya', 'regcreatekeyexa', 'regdeletevaluea'] 
callTypes['networking'] = ['wsacleanup', 'wsastartup', 'inet_addr', 'htons', 'socket', 'wsagetlasterror', 'bind', 'listen', 'accept', 'inet_ntoa', 'recv', 'recvfrom', 'closesocket', 'send', 'sendto', 'tcpseqmypspec', 'send_ip_packet_eth', 'winsock', 'traceroute', 'winpcap', 'tcpip']


def documentation():
    return {'description': desc, 'opts_doc': opts_doc, 'set': False, 'atomic': True}


def nextJump(insns, address):   
    jump = [instr for instr in insns if len(instr['mnem']) > 0 and instr['addr'] > address and instr['mnem'][0] == 'j' and instr['mnem'] != 'jmp'] 
    if jump:
        return jump[0]
    return []
    

def convert_rva_offset(oid, rva):
    header = api.get_field("object_header", oid, "header")
    try:
        rva = int(rva)
    except:
        raise ShellSyntaxError("Unrecognized address %s" % rva)
    return header.get_offset(rva)
                                

def prevJump(insns, address):   
    jump = [instr for instr in insns if len(instr['mnem']) > 0 and instr['addr'] < address and instr['mnem'][0] == 'j' and instr['mnem'] != 'jmp'] 
    if jump:
        return jump[0]
    return []


def forwardJump(jump, address):
    if not jump:
        return False
    if jump['d_op']['data'] > address:
        return True
    return False            
        
        
def correctCMP(instr):
    if instr['s_ops'] and type(instr['s_ops'][0]['data']) is int and type(instr['d_op']['data']) is str:
        return True
    elif instr['s_ops'] and type(instr['s_ops'][0]['data']) is str and type(instr['d_op']['data']) is int:
           return True
    if type(instr['d_op']['data']) is dict and 'base' in instr['d_op']['data'] and instr['d_op']['data']['base'] != None:
        return True
    else:
        for source in instr['s_ops']:
            if type(source['data']) is dict and 'base' in source['data'] and source['data']['base']!=None:
                return True
        return False
 

def analyzeCall(oid, features, address, block_address, insns, line):
    system_calls = api.get_field('map_calls', [oid], 'system_calls')
    internal_calls = api.get_field('map_calls', [oid], 'internal_functions')
    call = convert_rva_offset(oid, line['addr'])
    previousCalls = [instr for instr in insns if instr['addr'] < line['addr'] and instr['mnem'] == 'call']
    lastCall = 0
    if previousCalls:
        lastCall = max(previousCalls, key=lambda x:x['addr'])['addr']
    variables = [set([(instr['s_ops'][0]['data'] if type(instr['s_ops'][0]['data']) is not dict else instr['s_ops'][0]['data']['base']) for instr in insns 
                if 's_ops' in instr and instr['addr'] < line['addr'] and instr['addr'] > lastCall and instr['group'] == 'load'])]
    if call in system_calls:
        features[block_address]['functions'].append({system_calls[call]:variables})
        for callType, funcs in callTypes.iteritems():
            if system_calls[call].lower() in funcs:
                features[address].update({callType:True})
    elif call in internal_calls:
        features[block_address]['functions'].append({internal_calls[call]:variables})
    if line['d_op']['data'] == address:
        features[block_address].update({'recursion':True})


def analyzeConditionals(oid, features, block_address, insns, line, nesting):
    jump = nextJump(insns, line['addr'])
    pJump = prevJump(insns, line['addr'])
    prevAddress = 0
    if pJump:
        prevAddress = pJump['d_op']['data']
    if jump:
        if forwardJump(jump, line['addr']):
            condType = 'if'
        else:
            condType = 'loop'
        if jump['d_op']['data'] == prevAddress:
            nesting.append(condType)
        else:
            features[block_address]['conditional_structure'].append(nesting)
            nesting = [condType]


def checkDynamicCalls(oid, features):
    strs = api.retrieve('strings', [oid])
    strs = ''.join([strs[addr] for addr in sorted(strs)])
    for callType, funcs in callTypes.iteritems():
        for func in funcs:
            if func in strs.lower():
                features.update({'dynamic_'+callType:True})
                break
                
def process(oid, opts):
    logger.debug('process()')
    ifs = 0; loops = 0; conditionals = []; insns = []; features = {}; variables = []
    asm = api.retrieve('function_extract', [oid])
    if not asm:
        return False
    basic_blocks = api.retrieve('basic_blocks', [oid])
    for func_addresses, blocks in sorted(basic_blocks.iteritems()):
        features[func_addresses] = {}
        for block in blocks:
            features[func_addresses].update({block['first_insn']:{'functions':[], 'conditional_structure':[]}})
    for address, dicts in sorted(asm.iteritems()):
        previousAddr = 0
        nesting = []
        insns = dicts['insns']
        for line in insns:
            block_address = max([block_index for block_index in features[address] if block_index <= line['addr']])
            if line['mnem'] == 'call':
                analyzeCall(oid, features[address], address, block_address, insns, line)
            #if line['group'] == 'cond':
            #    analyzeConditionals(oid, features[address], block_address, insns, line, nesting)
        conditionals = [instr for instr in insns if instr['group'] == 'cond' and correctCMP(instr)] 
        loops = len([instr for instr in conditionals if not forwardJump(nextJump(insns, instr['addr']), instr['addr'])])
        ifs = len([instr for instr in conditionals if forwardJump(nextJump(insns, instr['addr']), instr['addr'])])                
        maths = len([instr for instr in insns if instr['group'] == 'arith'])
        features[address].update({'conditionals':len(conditionals), 'loops':loops, 'ifs':ifs, 'math':maths})
    checkDynamicCalls(oid, features)
    api.store(name, oid, features, opts)
    return True
        
        
