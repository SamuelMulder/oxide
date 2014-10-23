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

""" Plugin: Utility functions for manipulating files and collections
"""

import progress, api
import random, cPickle, os, zipfile, tarfile, gzip, tempfile, socket 
from collections import defaultdict 

proxy = None
random.seed()

def membership(args, opts):
    """ 
        Prints the set of collections to which a file belongs. 
                If a collection is passed its membership will not be printed
        Syntax: membership %<oid> ...
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    
    exclude_cids = [oid for oid in valid if api.exists("collections", oid)]
    main_oids = set(api.expand_oids(valid))
        
    membership_cids = {}
    cids = [cid for cid in api.collection_cids() if cid not in exclude_cids]
    for cid in cids:
        this_oids = set(api.expand_oids(cid))
        this_intersection = list(main_oids.intersection(this_oids))
        if this_intersection:
            membership_cids[cid] = this_intersection
            
    if "noprint" not in opts:
        print_membership(membership_cids)
                
    return membership_cids

def summarize(args, opts):
    """ 
        Gives a summary of a set of files, including types, extensions, etc.  If no argument
                is passed, gives a summary for the entire datastore (may be very slow).
        Syntax: summarize %<oid>
    """
    valid, invalid = api.valid_oids(args)
    valid = set(api.expand_oids(valid))
    types = defaultdict(int)
    extensions = defaultdict(int)
    sizes = [0,0,0,0,0,0]

    if not args:
        valid = set(api.retrieve_all_keys("file_meta"))
            
    for oid in valid:
        meta = api.retrieve("file_meta", oid)
        names = meta["names"]
        if names:
            for name in names:
                parts = name.split(".")
                if len(parts) > 1:
                    extensions[parts[-1]] += 1
                else:
                    extensions["None"] += 1
        t = api.get_field("src_type", oid, "type")
        if t: types[t] += 1
        size = meta["size"]
        if size < 1024: sizes[0] += 1
        elif size < 10*1024: sizes[1] += 1
        elif size < 100*1024: sizes[2] += 1
        elif size < 1024*1024: sizes[3] += 1
        elif size < 10*1024*1024: sizes[4] += 1
        else: sizes[5] += 1

    print "\nTotal files in set: ", len(valid)

    print "\nExtensions (files with multiple names counted more than once):"
    exts = extensions.keys()
    exts = sorted(exts, key=lambda val: extensions[val], reverse=True)
    for e in exts:
        print "  ", e, "   \t\t  :\t\t  ", extensions[e]
    print "\nTypes:"
    ts = types.keys()
    ts = sorted(ts, key=lambda val: types[val], reverse=True)
    for t in ts:
        print "  ", t, "   \t\t  :\t\t  ", types[t]

    print "\nSizes: "
    print "   Under 1k   :", sizes[0]
    print "   1k - 10k   :", sizes[1]
    print "   10k - 100k :", sizes[2]
    print "   100k - 1MB :", sizes[3]
    print "   1MB - 10MB :", sizes[4]
    print "   over 10 MB :", sizes[5]

    return None
    
def intersection(args, opts):
    """ 
        Returns the intersection of the collections passed in, non-collection IDs will be ignored
        Syntax: intersection &col1 &col2 ...
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    cids = [oid for oid in valid if api.exists("collections", oid)]
    if not cids:
        raise ShellSyntaxError("No valid collections found")
    oids = set(api.expand_oids(cids[0]))
    for c in cids[1:]:
        oids = oids.intersection(api.expand_oids(c))
    return oids
    
    
def file_io(args, opts):
    """ 
        store or retrieve contents of a Python data structure
        Syntax:
            file_io <file_name> | show     # Retrieve from a file
            @<var> | file_io <file_name>   # Write to a file
    """
    if not args:
        raise ShellSyntaxError("File name not specified")
        
    fname = args[0]
    args = args[1:]
    if args: # Writing to a file
        fd = open(fname, 'wb')
        cPickle.dump(args, fd)
        fd.close()
        return args
    
    else: # Reading from a file
        if not os.path.isfile(fname):
            raise ShellSyntaxError("File %s not found." % fname)
        fd = open(fname, 'rb')
        p = cPickle.load(fd)
        fd.close()
        return p
    
    
def clean(args, opts):
    """ 
        Passes a list where empty dict keys are removed
        Syntax: <some_command> | clean | ...
    """
    out = []
    for a in args:
        if not a:
            continue
        if isinstance(a, dict):
            bad_keys = []
            for k in a:
                if not a[k]:
                    bad_keys.append(k)
            for k in bad_keys:
                del a[k]
            out.append(a)
        else:
            out.append(a)
    return out


def expand(args, opts):
    """ 
        Passes a list where any cids passed are expanded to the oids in that collection 
        Syntax: &<my_collection> | expand | ...
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    return api.expand_oids(valid)
    

def random_sample(args, opts):
    """ 
        Given a list of oids passes a random subset of them
        syntax: random_sample <oid1> <oid2> ... <oidn> [--n=<size> | --p=<percent>]
                (default is 10%)
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    args = api.expand_oids(valid)
    if not args:
        return []

    nargs = len(args)
    n = int( round( nargs / float(10) ) )

    if "n" in opts:
        try:
            n = int(opts["n"])
            if n < 0: raise ValueError
            if n > nargs: n = nargs
        except ValueError:
            raise ShellSyntaxError("Invalid integer value for n: %s" % opts["n"])
    elif "p" in opts:
        try:
            p = float(opts["p"])
            if p <= 0 or p > 100: raise ValueError
        except ValueError:
            raise ShellSyntaxError("Invalid float value for p: %s" % opts["p"])
        n = int( round( len(args) / (100/p) ) )

    if n == 0: n = 1
    return random.sample(args, n)

def random_shuffle(args, opts):
    """ 
        Passes a randomized list of oids
        syntax: random_shuffle <oid1> <oid2> ... <oidn>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    args = api.expand_oids(valid)
    random.shuffle(args)
    return args

def top_n(args, opts):
    """ 
        Passes the top n (default is 10) items passed. (e.g. histogram)
        Syntax: <some_command | top_n [--n=<int>] | ...
    """
    if not args:
        return []
    n = 10
    if "n" in opts:
        n = opts["n"]

    if isinstance(args[0], (dict, defaultdict)):
        keys = args[0].keys()
        keys.sort(reverse=True, key=args[0].__getitem__)
        out = {}
        for i in keys[:n]:
           out[i] = args[0][i]
        return [out]

    else:
        args.sort()

    return args[:n]
  
      
def count(args, opts):
    """ 
        Prints the number of items passed. Passes whatever was passed.
        Syntax: <some_command> | count
    """
    print " - Received: ", len(args), " args."
    return args

def select(args, opts):
    """
        If passed a list of dictionaries, selects out the field indicated
        Syntax: select --field="field_name" 
    """
    if not args or not opts:
        return []
    if "field" in opts:
        field = opts["field"]
    else:
        return []
    new_args = []
    for a in args:
        if field in a and a[field]:
            new_args.append(a[field])
    return new_args

def export_file(args, opts):
    """ 
        Given a list of oid's exports the files. If tar or zip option used with
                multiple input files a single file will be exported.
        Syntax: export_file <oid1> <oid2> ... <oidn> [--zip | --tar [--bz2 | --gz] --name=<export_name> ]
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    oids = api.expand_oids(valid)
    
    if "zip" in opts:
        export_tar_zip(oids, opts, type="zip")
    elif "tar" in opts:
        export_tar_zip(oids, opts, type="tar")
    else:
        export_files(oids, opts)

def cat(args, opts):
    """ 
        Given an oid, displays the text of the file.  Should only be run on plain-text
                files.  Will give an error if file appears to not be plain-text.  Override with --force.
        Syntax: cat <oid>
    """
    import string
    
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    oids = api.expand_oids(valid)
    
    for o in oids:
        data = api.get_field("files", o, "data")
    
    printable = set(data).issubset(set(string.printable))
    if not printable and not "force" in opts:
        raise ShellSyntaxError("File contains non-printable characters.  Use --force to override.")
    else:
        print data
        
def size_filter(args, opts):
    """ 
        Filter files by size in bytes
        Syntax: size_filter %<oid> --min=<size> --max=<size>
    """
    if not args:
        raise ShellSyntaxError("File name not specified")
        
    min_size = 0
    max_size = None
    if "min" in opts:
        min_size = int(opts["min"])
    if "max" in opts:
        max_size = int(opts["max"])
        
    valid, invalid = api.valid_oids(args)
    oids = api.expand_oids(valid)
    filtered_oids = []
    for oid in oids:
        meta = api.retrieve("file_meta", oid)
        size = meta["size"]
        if size > min_size and ((not max_size) or size < max_size):
            filtered_oids.append(oid)
            
    return filtered_oids
    
def name_filter(args, opts):
    """ 
        Use without args to find files with that name, use with args to filter
        Syntax: name_filter %<oid> --name=<file_name>
    """
    if not "name" in opts:
        raise ShellSyntaxError("name_filter requires a --name=<file_name> option")
    
    oids = []
    valid, invalid = api.valid_oids(args)
    valid = api.expand_oids(valid)
    name = opts["name"]
    terms = name.split("*")
    
    if not args:
        if len(terms) == 1:
            return api.get_oids_with_name(opts["name"]).keys()
        else:
            valid = api.retrieve_all_keys("file_meta")
            
    if len(terms) == 1:
        for oid in valid:
            names = api.get_field("file_meta", oid, "names")
            if names and opts["name"] in names:
                oids.append(oid)
    else:
        for oid in valid:
            names = api.get_field("file_meta", oid, "names")
            if names:
                for name in names:
                    if name.startswith(terms[0]) and name.endswith(terms[1]):
                        oids.append(oid)
    return oids

def byte_filter(args, opts):
    """ 
        Use without args to find files with that byte_string, use with args to filter
        Syntax: byte_filter %<oid> --bytes=<byte_string>
    """
    if not "bytes" in opts:
        raise ShellSyntaxError("byte_filter requires a --bytes=<byte_string> option")

    oids = []
    valid, invalid = api.valid_oids(args)
    valid = api.expand_oids(valid)
    bytes = str(opts["bytes"])
    
    if not args:
        valid = api.retrieve_all_keys("files")
     
    for o in valid:
        data = api.get_field("files", o, "data")
        if data.find(bytes) != -1:
            oids.append(o)
    return oids
    
def type_filter(args, opts):
    """ 
        Use without args to find all files with that type, use with args to filter
        Syntax: type_filter %<oid> --type=[ PE | ELF | PDF | etc...]
    """
    if not "type" in opts:
        raise ShellSyntaxError("type_filter requires a --type=[ PE | ELF | PDF | etc...] option")

    oids = []
    valid, invalid = api.valid_oids(args)
    valid = api.expand_oids(valid)
    
    if not args:
        valid = api.retrieve_all_keys("files")
            
    for oid in valid:
        data = api.retrieve("src_type", oid)
        if data and data["type"].lower() == opts["type"].lower():
            oids.append(oid)
    return oids

def key_filter(args, opts):
    """ 
        Use to match the results of a module (module name required). Specify key and optionally value.
        Syntax: key_filter %<oid> --module=<mod_name> --key=<key> [--value=<value>]
    """
    if not "module" in opts or not "key" in opts:
        raise ShellSyntaxError("key_filter requires a --module=<mod_name> and a --key=<key> option")
    oids = []
    valid, invalid = api.valid_oids(args)
    valid = api.expand_oids(valid)
    
    if not args:
        valid = api.retrieve_all_keys("files")
            
    if "key" in opts and "value" in opts:
        oids = api.retrieve("substring_search", valid, 
            {"mod":opts["module"], "key":opts["key"], "value":opts["value"]})
    elif "key" in opts:
        oids = api.retrieve("key_search", valid, 
            {"mod":opts["module"], "key":opts["key"]})
    return oids
    
def extension_filter(args, opts):
    """ 
        Use without args to find files with that extension, use with args to filter
        Syntax: extension_filter %<oid> --ext=<extension>
    """
    if not "ext" in opts:
        raise ShellSyntaxError("extension_filter requires a --ext=<extension> option")
    
    oids = set()
    valid, invalid = api.valid_oids(args)
    valid = api.expand_oids(valid)
    ext = opts["ext"]
    
    if not args:
        valid = api.retrieve_all_keys("file_meta")
            
    for oid in valid:
        names = api.get_field("file_meta", oid, "names")
        if names:
            for name in names:
                parts = name.split(".")
                if len(parts) > 1 and parts[-1].lower() == ext.lower():
                    oids.add(oid)
    return list(oids)

    
exports = [random_sample, random_shuffle, top_n, count, expand, clean, file_io, membership, select,
           export_file, intersection, cat, summarize, size_filter, name_filter, byte_filter, type_filter, key_filter, extension_filter]

############## UTILS #########################################################
def export_tar_zip(oids, opts, type):
    name = "export"
    if "name" in opts:
        name = opts["name"] and opts["name"]
        
    if type == "tar" and not name.endswith(".tar"):
        name += ".tar"
        
    if type == "zip" and not name.endswith(".zip"):
        name += ".zip"
        
    mode = "w"
    if "bz2" in opts:
        mode += ":bz2"
        name += ".bz2"
    elif "gz" in opts:
        mode += ":gz"
        name += ".gz"
    
    fname = unique_scratch_file(name)
    xo = None
    if type == "tar":
        xo = tarfile.open(fname, mode=mode)
    if type == "zip":
        xo = zipfile.ZipFile(fname, mode=mode)
        
    tmp_files = []
    names = []
    for oid in oids:
        data = api.get_field("files", oid, "data")
        if not data:
            print "Not able to process %s" % oid
            continue
            
        name = api.get_field("file_meta", oid, "names").pop()
        names.append(name)
        t = tmp_file(name, data)
        tmp_files.append(t)
        if type == "tar":
            xo.add(t)
        if type == "zip":
            xo.write(t)
        
    xo.close()
    print " - File(s) %s exported to %s" % (", ".join(names), fname)
    
    for f in tmp_files:
        os.remove(f)


def export_files(oids, opts):
    base_name = "export"
    if "name" in opts and opts["name"]:
        base_name = opts["name"]

    for oid in oids:
        data = api.get_field("files", oid, "data")
        if not data:
            print "Not able to process %s" % oid
            continue
        name = api.get_field("file_meta", oid, "names").pop()
        name = base_name + "_" + name 
        write_file(name, data)
   
   
def unique_scratch_file(name):
    base_name = os.path.basename(name)
    name = os.path.join(api.scratch_dir, base_name)
    if os.path.exists(name):
        name = tempfile.mktemp(suffix="_"+base_name, dir=api.scratch_dir)
    return name 


def write_file(name, data):
    name = unique_scratch_file(name)
    fd = open(name, "wb")
    fd.write(data)
    fd.close()
    print " - File %s exported" % (name)    
    

def print_membership(membership_cids):
    print "  --- Membership: ---" 
    if not membership_cids:
        print "   <EMPTY>"
        return
        
    for cid in membership_cids:
        name = api.get_colname_from_oid(cid)
        print "  - %s: " % name
        for oid in membership_cids[cid]:
            names = ", ".join(list(api.get_names_from_oid(oid)))
            print "    - %s : %s" % (oid, names)


def tmp_file(name, data):
    tmp = unique_scratch_file(name)
    fd = file(tmp, 'wb')
    fd.write(data)
    fd.close()
    return tmp
