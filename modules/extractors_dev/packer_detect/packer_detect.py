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

import histogram

def detect_packer(file_meta, data):
    prob_packed = 0

    #Determining number of standard and non-standard section names
    ss_names = set(['.text', '.code', '.data', '.rdata', '.idata', '.edata', '.pdata', '.xdata', '.reloc', '.bss', '.rsrc', '.crt', '.tls', '.orpc', '.INIT', ',data1'])

    bad_ss_names = set(['.UPX0', '.UPX1', '.UPX2', '.aspack', '.asdata', '.packed', '.RLPack', 'Themida', '.ndata', '.Upack', '.perplex', '.pelock', '.Wpack', 'PEinject', 'PEPACK!!', '.petite', '.pack32'])

    my_sections = set()
    #shouldn't really have any of these
    rwx_sections = 0
    #should only really have one of these
    execute_sections = 0
    #Should be high
    num_imports = 0
    num_bad_ss = 0
    num_sections = 0
    exec_sect_entropy = set()
    if not 'section_table' in file_meta:
        return None

    sections = file_meta['section_table']
    
    for section  in sections:
        flags = sections[section]['characteristics']
        if flags['MEM_READ'] and flags['MEM_WRITE'] and flags['MEM_EXECUTE']:
            rwx_sections = rwx_sections + 1

        if flags['MEM_EXECUTE']:
            execute_sections = execute_sections + 1
            offset = sections[section]["pointer_to_raw_data"]
            size = offset+sections[section]["size_of_raw_data"]
            section_data = data[offset:size]
            e = histogram.calc_entropy(section_data)
            exec_sect_entropy.add((section, e))
            if e > .9:
                prob_packed = prob_packed + 1
                
        my_sections.add(section.strip("\x00"))
        num_sections = num_sections + 1
        
    if not file_meta['import_table']:
        prob_packed = prob_packed + 1

    elif len(file_meta['import_table']) < 10:
        prob_packed = prob_packed + 1

    if execute_sections > 1:
        prob_packed = prob_packed + 1

    if execute_sections is 0:
        prob_packed = prob_packed + 1

    if rwx_sections > 0:
        prob_packed = prob_packed + 1


    num_sections = len(my_sections)
    num_nonstandard = len(my_sections.difference(ss_names))
    num_standard = len(my_sections.intersection(ss_names))
    num_bad = len(my_sections.intersection(bad_ss_names))
    
    if num_bad_ss > 0:
        prob_packed = prob_packed + 1

    if num_nonstandard > 0:
        prob_packed = prob_packed + 1


    if prob_packed > 2:
        return {'is_packed': True, 'num_standard_sect_names': num_standard, 'num_known_bad_sect_names': num_bad_ss, 'num_nonstandard_sect_names': num_nonstandard, 'num_rwx_sects': rwx_sections, 'num_exec_sections': execute_sections, 'num_imports': num_imports, 'executable_sect_entropy': exec_sect_entropy}
    else:
        return {'is_packed': False, 'num_standard_sect_names': num_standard, 'num_known_bad_sect_names': num_bad_ss, 'num_nonstandard_sect_names': num_nonstandard, 'num_rwx_sects': rwx_sections, 'num_exec_sections': execute_sections, 'num_imports': num_imports, 'executable_sect_entropy': exec_sect_entropy}
