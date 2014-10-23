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

import logging
name = "tags"
logger = logging.getLogger(name)

import api

def apply_tags(oid_list, new_tags):
    if isinstance(oid_list, list):
        for oid in oid_list:
            apply_tags(oid, new_tags)
    else:
        oid = oid_list
        if not api.exists("tags", oid):
            tags = {}
        else: 
            tags = api.retrieve("tags", oid, {}, True)
        for tag in new_tags:
            tags[tag] = new_tags[tag]
        api.store("tags", oid, tags)
        

def get_tags(oid):
    if not isinstance(oid, str):
        logger.error("get_tags must be called with a single OID")
        return None
    elif not api.exists("tags", oid):
        return None
    else:
        return api.retrieve("tags", oid)
        
        
def tag_filter(oid_list, tag, value="<empty>"):
    filtered_oids = []
    if not oid_list:
        oid_list = api.retrieve_all_keys("files")
        if not oid_list:
            logger.error("No files exist")
            return None
        cids = api.retrieve_all_keys("collections")
        if cids:
            oid_list.extend(cids)
            
    for oid in oid_list:
        t = get_tags(oid)
        if t and tag in t:
            if t[tag] == "<empty>" or value == "<empty>" or value == t[tag] or value in t[tag]:
                filtered_oids.append(oid)
                
    return filtered_oids
 