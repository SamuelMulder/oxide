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

""" Plugin: Functions to aid in the extraction of packed files
"""

import api, progress, sys_utils
import os, shutil, zipfile, tarfile, subprocess, commands, tempfile

upx_found = True
if subprocess.os.system("upx > /dev/null 2>&1") != 256:
    print " - UPX not found on this system, the upx plugin will not be available."
    upx_found = False
    

def ispacked(args, opts):
    """ 
        Pass a list of files that are packed
        Syntax: ispacked <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    valid = api.expand_oids(valid)

    if not "packer_detect" in api.modules_list():
        raise ShellRaiseError("packer_detect module not found")

    returns = []
    for oid in valid:
        res = api.get_field("packer_detect", oid, "is_packed") 
        cname = api.get_field("file_meta", oid, "names").pop()
        if res:
            returns.append(oid)
            print cname, " is packed."
        else:
            print cname, " is not packed."
    return returns


def import_archive(args, opts):
    """ 
        Import the contents of a archive (zip and tar) files. 
                Does not import the archive file itself.
                Passes a list of imported oids.
                
        Syntax: import_archive <file> | <dir>
    """
    if not args:
        raise ShellSyntaxError("No files/dir passed")

    oids = []
    oids.extend(import_zip(args, opts))
    oids.extend(import_tar(args, opts))
    if oids:
        unarchive(oids, opts)
    return oids
   
     
def import_zip(args, opts):
    """ 
        Import the contents of a zip file. Does not import the zip file itself.
                Passes a list of imported oids.
        Syntax: import_zip <file> | <dir>
    """
    if not args:
        raise ShellSyntaxError("No files/dir passed")
    
    oids = []
    newfiles = []
    for arg in args:
        if os.path.isdir(arg):
            print " - Processing zip files in directory %s ..." % arg
            files = sys_utils.get_files_from_directory(arg)
            p = progress.progress(len(files))
            for f in files:
                zoids, noids = import_zipfile(f)
                oids.extend(zoids)
                newfiles.extend(noids)
                p.tick()
                
        elif os.path.isfile(arg):
            print " - Attempting to unzip file %s" % arg
            zoids, noids = import_zipfile(arg)
            oids.extend(zoids)
            newfiles.extend(noids)
    
        else:
            print " - %s not found" % (arg)
    
    print " - Extracted %d files %d are new" % (len(oids), len(newfiles))
    if oids:
        oids.extend(unzip(oids, opts))
        
    return oids
    
def import_tar(args, opts):
    """ 
        Import the contents of a tar file. Does not import the tar file itself.
                Passes a list of imported oids.
        Syntax: import_tar <file> | <dir>
    """
    if not args:
        raise ShellSyntaxError("No files/dir passed")
    
    oids = []
    newfiles = []
    for arg in args:
        if os.path.isdir(arg):
            print " - Processing tar files in directory %s" % arg
            files = sys_utils.get_files_from_directory(arg)
            p = progress.progress(len(files))
            for f in files:
                toids, noids = import_tarfile(f)
                oids.extend(toids)
                newfiles.extend(noids)
                p.tick()
                
        elif os.path.isfile(arg):
            print " - Attempting to untar file %s" % arg
            toids, noids = import_tarfile(arg)
            oids.extend(toids)
            newfiles.extend(noids)
    
        else:
            print " - %s not found" % (arg)
    
    print " - Extracted %d files %d are new" % (len(oids), len(newfiles))
    if oids:
        oids.extend(untar(oids, opts))
    
    return oids
    

def import_upx(args, opts):
    """ 
        Import the contents of a upx file. Does not import the upx file itself.
                Passes a list of imported oids.
    """
    if not args:
        raise ShellSyntaxError("No files/dir passed")
    
    oids = []
    newfiles = []
    for arg in args:
        if os.path.isdir(arg):
            print " - Processing upx files in directory %s" % arg
            files = sys_utils.get_files_from_directory(arg)
            p = progress.progress(len(files))
            for f in files:
                uoids, noids = import_upxfile(f)
                oids.extend(uoids)
                newfiles.extend(noids)
                p.tick()
                
        elif os.path.isfile(arg):
            print " - Processing file %s ..."
            uoids, noids = import_upxfile(arg)
            oids.extend(uoids)
            newfiles.extend(noids)
    
        else:
            print " - %s not found" % (arg)
    
    print " - Extracted %d files %d are new" % (len(oids), len(newfiles))
    return oids


def unarchive(args, opts):
    """ 
        Try in unarchive (unzip and untar), passes a list of ununarchived oids
        Syntax: unarchive <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
        
    oids = api.expand_oids(valid)
    unarchived = []
    newfiles = []

    print " - Attempting to unarchive (zip, tar) %d files" % len(oids)
    p = progress.progress(len(oids))
    for oid in oids:
        data = api.get_field(api.source(oid), oid, "data")
        if not data:
            print "Not able to process %s" % (oid)
            p.tick()
            continue
            
        tmp = tmp_file(oid, data)
        if not tmp: continue
        aoids = []
        noids = []
        
        if tarfile.is_tarfile(tmp): # tar
            print " - Unpacking a tar file"
            aoids, noids = import_tarfile(tmp, parent_oid=oid)

        elif zipfile.is_zipfile(tmp): # zip
            print " - Unpacking a zip file"
            aoids, noids = import_zipfile(tmp, parent_oid=oid)
            
        unarchived.extend(aoids)
        newfiles.extend(noids)
        os.remove(tmp)
        p.tick()
        
    if unarchived:
        unarchived.extend(unarchive(unarchived, opts)) # Unpacked children

    print " - Extracted %d files %d are new" % (len(unarchived), len(newfiles))
    return unarchived
    
    
def untar(args, opts):
    """ 
        Try to untar items passed, passes a list of untarred oids
        Syntax: untar <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")

    oids = api.expand_oids(valid)
    untarred = []
    newfiles = []

    p = progress.progress(len(oids))
    print " - Attempting to untar %d files" % len(oids)
    for oid in oids:
        src = api.source(oid)
        data = api.get_field(src, oid, "data")
        if not data:
            print "No data found for %s" % (oid)
            p.tick()
            continue   
             
        tmpname = oid + ".tar.tmp"
        tmp = tmp_file(tmpname, data) 
        if not tmp: continue
        if tarfile.is_tarfile(tmp):
            toids, nfiles = import_tarfile(tmp, parent_oid=oid)
            untarred.extend(toids)
            newfiles.extend(nfiles)
            
        os.remove(tmp)
        p.tick()
    
    if untarred:
        untarred.extend(untar(untarred, opts)) # Untar children
        
    print " - %d files extracted, %d files are new" % (len(untarred), len(newfiles))
    return untarred
        

def unzip(args, opts):
    """ 
        Try to unzip items passed, passes a list of unzipped oids
        Syntax: unzip <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    oids = api.expand_oids(valid)
    unzipped = []
    newfiles = []

    p = progress.progress(len(oids))
    print " - Attempting to unzip %d files" % len(oids)
    for oid in oids:
        data = api.get_field(api.source(oid), oid, "data")
        if not data:
            print "No data found for %s" % (oid)
            p.tick()
            continue
            
        tmpname = oid + ".zip.tmp"    
        tmp = tmp_file(tmpname, data)
        if not tmp: continue
        if zipfile.is_zipfile(tmp):
            zoids, noids = import_zipfile(tmp, parent_oid=oid)
            unzipped.extend(zoids)
            newfiles.extend(noids)
            
        os.remove(tmp)
        p.tick()
        
    if unzipped:
        print " - %d files extracted, %d files are new" % (len(unzipped), len(newfiles))
        print 
        unzipped.extend(unzip(unzipped, opts)) # Unzip children
    
    return unzipped


def upx(args, opts):
    """ 
        Try to upx unpack items passed, passes a list of unpacked oids
        Syntax: upx <oid_1> <oid_2> ... <oid_n>
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
        
    oids = api.expand_oids(valid)
    unupx = []
    newfiles = []
    
    p = progress.progress(len(oids))
    print " - Attempting to UPX unpack %d files" % len(oids)
    for oid in oids:
        data = api.get_field(api.source(oid), oid, "data")
        if not data:
            print "No data found for %s" % (oid)
            p.tick()
            continue
        
        meta = api.retrieve("file_meta", oid)
        name = meta["names"].pop()
        tmpname = name + ".unpacked_upx"
        tmp = tmp_file(tmpname, data)
        if not tmp: continue
        if is_upx(tmp):
            uoids, noids = import_upxfile(tmp, parent_oid=oid)
            unupx.extend(uoids)
            newfiles.extend(noids)
            
        os.remove(tmp)
        p.tick()
    
    print " - %d files extracted, %d are new" % (len(unupx), len(newfiles))
    return unupx

def extract_osx(args, opts):
    """
        Imports objects from an OSX Universal Binary
        Syntax:
    """
    valid, invalid = api.valid_oids(args)
    if not valid:
        raise ShellSyntaxError("No valid oids found")
    args = api.expand_oids(valid)
    for oid in args:
        meta = api.retrieve("file_meta", oid)
        name = meta["names"].pop()
        
        src_type = api.retrieve("src_type", oid)
        if src_type["type"] != "OSX Universal Binary":
            print "  - %s (%s) is not an OSX Universal binary file, skipping" % (name, oid)
            continue
        

        
        data = api.retrieve("files", oid)["data"] 
        if not data:
            print "  - No data for this file %s (%s) " % (name, oid)
            continue
            
        oh = api.retrieve("object_header", oid)
        num = oh["header"].num_embedded
        print "  - Found %s files embedded in file %s (%s)" % (num, name, oid)
        
        oids = []
        newfiles = 0
        for f in oh["header"].embedded:
            beg = f.header_offset
            end = f.file_end
            print "    + Extracting bytes %s:%s of file type %s" % (beg, end, f.machine) 
            
            fname = name + "_" + f.machine
            fpath = os.path.join(api.scratch_dir, fname)
            
            print "    + Writing temp file to %s" % (fpath)
            fd = file(fpath, 'wb')
            fd.write(data[beg:end])
            fd.close()
            
            print "    + Importing file %s" % (fpath)
            oid, newfile = api.import_file(fpath)
            oids.append(oid)
            if newfile: newfiles += 1
            
            print "    + Removing temp file from the scratch directory"
            os.remove(fpath)
            print
            
            
        print "  - Extracted and imported %s files, %s were new" % (len(oids), newfiles) 
        
        # Return a list of the oids corresponding to the files extracted
        return oids
        

exports = [unzip, ispacked, untar, unarchive, import_zip, import_tar, import_archive, extract_osx]
if upx_found: # Don't export upx if not found on this system
    exports.extend( [ upx, import_upx] )
    
####### UTILITIES ##############################################################
def import_upxfile(fname, parent_oid=None):
    """ Given a file try to upx unpack it and import the extracted file,
        return the an oid list and a newfiles list.
        If parent_oid is passed tag the parent and the children.
    """
    newfiles = []
    
    if not is_upx(fname):
        return [], newfiles
    
    unpackcmd = "upx -d " + fname + " -qqq"
    if int(subprocess.os.system(unpackcmd)) != 0:
        print " - Not able to decompress file %s" % fname
        return [], newfiles
        
    unpacked_oid, newfile = api.import_file(fname)
    if not unpacked_oid:
        print " - Not able to import file %s" % fname
        return [], newfiles
        
    if newfile:
        newfiles.append(unpacked_oid)
    
    if parent_oid:
        tag_append(unpacked_oid, "upx_unpacked", parent_oid)
        tag_append(parent_oid, "upx_packed", unpacked_oid)
    
    return [unpacked_oid], newfiles


def import_tarfile(fname, parent_oid=None):
    """ Given a file try to untar it and import the extracted files,
        return the an oid list and a newfiles list.
        If parent_oid is passed tag the parent and the children.
    """
    oids = []
    newfiles = []
    import api
    if not tarfile.is_tarfile(fname):
        return oids, newfiles
        
    tf = tarfile.open(fname)
    
    for t in tf.getmembers():
        if not t.isfile(): # Skip dirs and links
            continue
            
        tar_out = os.path.join(api.scratch_dir, t.name)
        try:
            tf.extract(member=t, path=api.scratch_dir)
        except:
            print " - Not able to extract file %s from tarfile %s" % (f, fname)
            continue
            
        oid, newfile = api.import_file(tar_out)
        if not oid:
            print " - Not able to import file %s" % fname
            os.remove(tar_out)
            continue
            
        if newfile:
            newfiles.append(oid)
        
        if parent_oid:
            tag_append(oid, "untarred", [parent_oid])
            
        os.remove(tar_out)
        oids.append(oid)
    
    if parent_oid and oids:
        tag_append(parent_oid, "tarred", oids)
    
    return oids, newfiles


def import_zipfile(fname, parent_oid=None):
    """ Given a file try to unzip it and import the extracted files,
        return the an oid list and a newfiles list.
        If parent_oid is passed tag the parent and the children.
    """
    oids = []
    newfiles = []
                
    if not zipfile.is_zipfile(fname):
        return oids, newfiles

    zf = zipfile.ZipFile(fname)
    for f in zf.namelist():
        try:
            zip_out = zf.read(f)
        except:
            print " - Not able to extract file %s from zipfile %s" % (f, fname)
            continue

        zout_tmp = tmp_file(f, zip_out)
        if not zout_tmp: continue
        oid, newfile = api.import_file(zout_tmp)
        if not oid:
            print " - Not able to import file %s" % fname
            os.remove(zout_tmp)
            continue
            
        if newfile:
            newfiles.append(oid)
        
        if parent_oid:
            tag_append(oid, "unzipped", [parent_oid])
            
        os.remove(zout_tmp)
        oids.append(oid)
    
    if parent_oid and oids:
        tag_append(parent_oid, "zipped", oids)
    
    return oids, newfiles
    
    
def is_upx(fname):
    if commands.getoutput("upx -t "+fname).find("[OK]") == -1:
        return False
    else:
        return True
    
    
def tag_append(oid, tag, value):
    """ Create or append a tag:value entry for a given oid
    """
    tags = api.get_tags(oid)
    if not tags or tag not in tags: # First time this tag is being applied
        api.apply_tags(oid, {tag:value})
        return True
        
    values = tags[tag]
    if not isinstance(values, list):
        values = [values]
    values = set(values)
    if not isinstance(value, list):
        value = [value]
    values.update(value)
    values = list(values)
    api.apply_tags(oid, {tag:values})
    return True
    

def tmp_file(name, data):
    """ Given a file name and data uses the Python tempfile package to write the file to
        the scratch directory.
    """
    if not data:
        return None
    fname = os.path.basename(name)
    tmp = os.path.join(api.scratch_dir, fname)
    if os.path.exists(tmp):
        tmp = tempfile.mktemp(prefix=fname, dir=api.scratch_dir)
    fd = file(tmp, 'wb')
    fd.write(data)
    fd.close()
    return tmp