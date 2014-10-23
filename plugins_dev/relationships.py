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
family = None

def relationships(args, opt):
    """ Plugin: Pring zip and upx file relationships including parents' childrens' parents' childrens' ...
        Syntax: relationships <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    oids = api.expand_oids(valid)
    global family
    for oid in oids:
        family = {}
        no_parents = set()
        build_ancesstors([oid])
        build_decendants(family.keys())
        name = api.get_field("file_meta", oid, "names").pop()
        print
        print " -- File Relationships for %s --" % name 
        print_relationships()
        
    
exports = [relationships]

############### UTILITIES ######################################################
def build_ancesstors(entities):
    for e in entities:
        if e in family:
            continue

        family[e] = get_kids(e)
        parents = get_parents(e)
        if parents:
            build_ancesstors(parents)

        build_ancesstors(family[e])

    
def build_decendants(entities):
    for e in entities:
        kids = get_kids(e)
        family[e] = kids
        for kid in kids: 
            if not kid in family:
                build_decendants(family[e])
    

def get_parents(oid):
    parents = set()
    tags = api.get_tags(oid)
    if not tags:
        return parents

    if "untarred" in tags:
        tag = tags["untarred"]
        parents.update(tag)
        if isinstance(tag, list):
            parents.update(tag)
        else:
            parents.add(tag)
                    
    if "unzipped" in tags:
        tag = tags["unzipped"]
        parents.update(tag)
        if isinstance(tag, list):
            parents.update(tag)
        else:
            parents.add(tag)
            
    if "upx_unpacked" in tags:
        tag = tags["upx_unpacked"]
        if isinstance(tag, list):
            parents.update(tag)
        else:
            parents.add(tag)
            
    return parents


def get_kids(oid):
    kids = set()
    tags = api.get_tags(oid)
    if not tags:
        return kids
    
    if "tarred" in tags:
        tag = tags["tarred"]
        if isinstance(tag, list):
            kids.update(tag)
        else:
            kids.add(tag)
    
    if "zipped" in tags:
        tag = tags["zipped"]
        if isinstance(tag, list):
            kids.update(tag)
        else:
            kids.add(tag)
            
    if "upx_packed" in tags:
        tag = tags["upx_packed"]
        if isinstance(tag, list):
            kids.update(tag)
        else:
            kids.add(tag)
            
    return kids


def print_relationships():
    no_relationships = True
    for e in family:
        if not family[e]:
            continue
        no_relationships = False
        name = api.get_field("file_meta", e, "names").pop()
        kid_names = []
        for kid in family[e]:
            kid_names.append(api.get_field("file_meta", kid, "names").pop())
        print "   -", name, "->", ", ".join(kid_names)
    if no_relationships:
        print "   < NONE >"
    print
