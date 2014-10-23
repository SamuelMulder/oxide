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

import sys, os, shutil
import _path_magic
import core.oxide as oxide

def extract_ordinal(f):
    oid = oxide.import_file(f)[0]
    if not oid:
        print " - Not able to import the file %s" % f
        return None

    print " - Processing %s %s" % (f, oid)
    exports = oxide.get_field("pe_parse", oid, "exports_table")
    if not exports:
        print "    ... No exports, skipping"
        return None

    file_data = oxide.get_field("files", oid, "data")
    ordinals = {}

    for name in exports["export_names"]:
        ordinals[exports["export_names"][name]['ord']] = name

    return ordinals

    
if __name__ == "__main__":
    if not len(sys.argv) > 1:
        print " - Must provide a file or files (e.g. *.dll)"
        sys.exit()

    print " - Moving datastore to the scratch dir"
    oxide.datastore.datastore_dir = os.path.join(oxide.config.dir_scratch, "db")
    oxide.config.dir_datastore = oxide.datastore.datastore_dir
    if os.path.isdir(oxide.datastore.datastore_dir):
        shutil.rmtree(oxide.datastore.datastore_dir)
    oxide.sys_utils.assert_dir_exists(oxide.datastore.datastore_dir)

    files = sys.argv[1:]
    files.sort()
    
    ordinal_map = os.path.join(oxide.config.dir_reference, "ordinal_map")
    print " - Loading existing oridinal map %s" % ordinal_map
    ordinal_db = {}
    if os.path.isfile(ordinal_map):
        ordinal_db = oxide.sys_utils.read_object_from_file(ordinal_map)
    
    if len(files) < 10:
        print " - Extracting ordinal name map from %s"  % ", ".join(files)
    else:
        print " - Extracting ordinal name map from %s files" % len(files)
        
    for f in files:
        if not os.path.isfile(f):
            print " - File %s does not exist, skipping." % f
            continue
        ordinals = extract_ordinal(f)
#        print f, " : ", ordinals
        if ordinals:
            name = os.path.basename(f)
            ordinal_db[name] = ordinals
            
    print " - Saving results to %s" % ordinal_map
    oxide.sys_utils.write_object_to_file(ordinal_map, ordinal_db)
             
    print " - Removing temp datastore in the scratch dir" 
    shutil.rmtree(oxide.datastore.datastore_dir)
    print " - Done"
