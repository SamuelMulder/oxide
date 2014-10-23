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

import _path_magic, os
from core import config

# Ignore builtin modules
ignore = ["logging", "os", "sys", "math", "time", "unittest", "glob", 
          "string", "hashlib", "pprint", "struct", "random", "collections", 
          "StringIO", "as"]
ignore = set(ignore)

# Ignore core modules
for c in os.listdir("core"):
    if c.endswith(".py"):
        ignore.add(c.rstrip(".py"))

def get_imports(file_location):
    imports = []
    fd = open(file_location, "r")
    lines = fd.readlines()
    fd.close()
    quote = False
    for l in lines:
    
        # Ignore triple quote strings
        if l.find('"""') != -1 and quote:
            quote = False
            continue
        elif l.find('"""') != -1:
            quote = True
            continue
        elif quote:
            continue
            
        # Ignore pound quotes strings
        if l.find("#") != -1:
            l = l[:l.find("#")].strip()
            
            
        # Ignore the keyword 'as' (e.g. import foo as bar)
        if l.find(" as ") != -1:
            l = l[:l.find("as")].strip()

        # get import statements
        if l.find("import ") != -1:
            if l.find("from ") != -1:
                i = l.strip("from").split()[0]
                if i not in ignore:
                    imports.append(i)
            else:
                for i in l.strip("import").split():
                    i = i.rstrip(",")
                    i = i.strip()
                    if i not in ignore:
                        imports.append(i)
            continue
    return imports


def get_dependencies(file_location):
    imports = []
    fd = open(file_location, "r")
    lines = fd.readlines()
    fd.close()
    quote = False
    for l in lines:
    
        # Ignore triple quote strings
        if l.find('"""') != -1 and quote:
            quote = False
            continue
        elif l.find('"""') != -1:
            quote = True
            continue
        elif quote:
            continue
            
        # Ignore pound quotes strings
        if l.find("#") != -1:
            l = l[:l.find("#")].strip()
            
        # Get retrieve calls
        if l.replace(" ","").find("api.retrieve") != -1:
            i = l[l.find("retrieve")+8:].lstrip("(").partition(",")[0].strip().strip("'").strip('"')
            if i != "name": # Ignore self calls - this will break if name equals something else
                imports.append(i)
        
        # Get process calls
        elif l.replace(" ","").find("api.process") != -1:
            i = l[l.find("process")+7:].lstrip("(").partition(",")[0].strip().strip("'").strip('"')
            if i != "name": # Ignore self calls - this will break if name equals something else
                imports.append(i)
         
        # Get get_field calls
        elif l.replace(" ","").find("api.get_field") != -1:
            i = l[l.find("get_field")+9:].lstrip("(").partition(",")[0].strip().strip("'").strip('"')
            if i != "name": # Ignore self calls - this will break if name equals something else
                imports.append(i)
         
                  
    return imports


def get_imps():
    imps = {}
    for (path, dirs, files) in os.walk(config.dir_modules):
        for f in files:
            fullpath = os.path.join(path, f)
            if fullpath.endswith(".py"):
                imports = get_imports(fullpath)
                imps[fullpath.replace(config.dir_modules, "")] = imports
    return imps

def get_deps():
    deps = {}
    for (path, dirs, files) in os.walk(config.dir_modules):
        for f in files:
            fullpath = os.path.join(path, f)
            if fullpath.endswith(".py"):
                imports = get_dependencies(fullpath)
                deps[fullpath.replace(config.dir_modules, "")] = imports
    return deps
        
def print_deps(deps):
    keys = deps.keys()
    keys.sort()
    for d in keys:
        if deps[d]:
            print d, "->", ", ".join(deps[d])

if __name__ == "__main__":
    print "Module dependencies: "
    print_deps(get_deps())
    print "\n\n\n\nModule Imports: "
    print_deps(get_imps())
