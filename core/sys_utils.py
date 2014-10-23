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

import os, api, sys, cPickle, marshal, zlib, logging, xmlrpclib, subprocess, time, tempfile

name      = "sys_utils"
logger    = logging.getLogger(name)
this_file =  __file__
this_dir  = os.path.split(this_file)[0]
oxide_dir = os.path.abspath(this_dir)
root_dir  = os.path.split(this_dir)[0]    
files_not_imported = [".DS_Store", ".gitignore"] # Files to ignore on import 
os.umask(0000) # Needed for file/directory creation

########### File related functions ############################################
def import_file(file_location, max_file_size):
    logger.debug("Importing file %s", file_location)

    if os.path.basename(file_location) in files_not_imported:
        logger.debug("Skipping the import of file: %s", file_location)
        return None

    if not os.path.isfile(file_location):
        logger.error("%s file does not exist.", file_location)
        return None
        
    elif not os.access(file_location, os.R_OK):
        logger.error("%s file is not accessable.", file_location)
        return None

    file_stat = get_file_stat(file_location)
    if not file_stat:
        logger.error("Cannot stat file %s.", file_location)
        return None

    filesize = os.path.getsize(file_location)/1048576.
    if filesize > max_file_size or filesize == 0:
        logger.error("File size %dM exceeds max filesize %dM or is 0", filesize, max_file_size)
        return None

    logger.debug("File import size %dM", filesize)
    data = get_contents_of_file(file_location)
    file_data = {"file_stat":file_stat, "size":filesize, "data":data}
    return file_data

def delete_file(file_location):
    if not os.path.isfile(file_location):
        logger.error("File does not exist:%s", file_location)
        return False

    try:
        os.remove(file_location)
        return True
        
    except OSError:
        logger.error("Cannot remove file:%s", file_location)
        return False
        
def get_file_stat(file_location):
    if not os.path.isfile(file_location):
        if os.path.islink(file_location):
            logger.warning("Skipping import of link:%s", file_location)
        else:
            logger.warning("File does not exist:%s", file_location)
        return None
        
    try:
        file_stat = os.stat(file_location)
        fs_dict = { "atime":file_stat.st_atime,
                    "mtime":file_stat.st_mtime,
                    "ctime":file_stat.st_ctime,
                    "size":file_stat.st_size,
                   }
        return fs_dict
        
    except OSError:
        logger.error("Cannot stat file:%s", file_location)
        return None
        
def get_contents_of_file(file_location):
    """ Given the location of a file return the contents or False if an error
        occurs.
    """
    try:
        f = file(file_location, 'rb')
        data = f.read()
        f.close()
        return data
        
    except IOError, err:
        logger.error("IOError:" + str(err))
        return None

def read_object_from_file(filename):
    """ Reads Python object from file by first uncompressing, unpickling, then returning results """
    if not os.path.isfile(filename):
        logger.error("%s does not exist.", filename)
        return None
        
    try:
        fd = file(filename, 'rb')
        data = fd.read()
        fd.close()
        try:
            udata = zlib.decompress(data)
            udata = cPickle.loads(udata)
            return udata
        except:
            data = cPickle.loads(data)
            return data
        
    except IOError, err:
        logger.error("IOError:%s", err)
        return None
    
    except cPickle.UnpicklingError, err:
        logger.error("UnpicklingError:%s", err)
        return None

def write_object_to_file(filename, data):
    """ Writes Python object to file by first pickling, compressing, then writing results """
    try:
        fd = file(filename, 'wb')
        data = cPickle.dumps(data)
        data = zlib.compress(data, zlib.Z_BEST_SPEED)
        fd.write(data)
        fd.close()
        logger.debug("Data stored to %s", filename)
        return True
        
    except IOError, err:
        logger.error("IOError:%s", err)
        return False
    except cPickle.PicklingError, err:
        logger.error("PicklingError:%s", err)
        return False

def get_files_from_directory(directory):
    """ Given the name of a directory return a list of the fullpath files in the
        given directory and subdirectories 
    """
    if not os.path.isdir(directory):
        return None
    elif not os.access(directory, os.R_OK|os.X_OK):
        logger.error("%s directory is not accessable.", directory)
        return None
    else:
        fullpath_files = []
        for (path, dirs, files) in os.walk(directory):
            for f in files:
                fullpath = os.path.join(path, f)
                fullpath_files.append(fullpath)
                
        return fullpath_files

def assert_dir_exists(directory):
    """ If directory does not exist create it"""
    if not os.path.isdir(directory) and not os.path.islink(directory):
        logger.debug("Creating directory %s", directory)
        try:
            os.makedirs(directory, mode=0777)
        except OSError:
            logger.debug("Already creating directory %s", directory)        
    return True    
         
########### Networking related functions #######################################
def pack(data):
    try:
        data = cPickle.dumps(data)
        data = zlib.compress(data, zlib.Z_BEST_SPEED)
        return xmlrpclib.Binary(data)
    except MemoryError:
        logger.error("Not able to pack data")
        return None
        
def unpack(data):
    try:
        if not data:
            return None
        data = data.data
        data = zlib.decompress( str(data) )
        return cPickle.loads(data)
    except MemoryError:
        logger.error("Not able to unpack data using cPickle.")
        return None

def pack_file(data):
    try:
        data = marshal.dumps(data)
        data = zlib.compress(data, zlib.Z_BEST_SPEED)
        return xmlrpclib.Binary(data)
    except MemoryError:
        logger.error("Not able to pack file data")
        return None
        
def unpack_file(data):
    try:
        if not data:
            return None
        data = data.data
        data = zlib.decompress( str(data) )
        return marshal.loads(data)
    except MemoryError:
        logger.error("Not able to unpack file data using cPickle.")
        return None

########### Print/Log/Setup support functions #######################################
def which(program):
    import os
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
    
def msg(s):
    print >> sys.stderr, s
    return

def error(s):
    print >> sys.stderr, s
    exit(1)
    
def log(h,s,o,f="output.log",cwd=None):
    log = open(f, "a")
    sys.stdout.write(h)
    sys.stdout.flush()
    
    if o == False:
        if cwd == None:
            p = subprocess.Popen(s, shell=True, stdout=log, stderr=log)
        else:
            p = subprocess.Popen(s, shell=True, stdout=log, stderr=log, cwd=cwd)
        
        while p.poll() is None:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1)
        if p.returncode == 0:
            msg("...success!")
            log.close()
            return True
        msg("...fail!")
        log.close()
        return False
    else:
        p = subprocess.Popen(s, shell=True)
        
        while p.poll() is None:
            sys.stdout.flush()
            time.sleep(1)
            
        if p.returncode == 0:
            msg("...success!")
            log.close()
            return True
        msg("...fail!")
        log.close()
        return False

def query(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer."""

    valid = {"yes":True, "y":True, "ye":True, "no":False, "n":False}

    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

########### Tempfile support functions #######################################
def tmp_file(name, data, empty=False, override=False):
    """ Given a file name and data uses the Python tempfile package to write the file to
        the scratch directory.
    """
    if not data and not empty:
        return None

    fname = os.path.basename(name)
    tmp = os.path.join(api.scratch_dir, fname)

    if os.path.exists(tmp):
        if override:
            os.remove(tmp)
        else:
            tmp = tempfile.mktemp(prefix=fname, dir=api.scratch_dir)

    if not empty:
        fd = file(tmp, 'wb')
        fd.write(data)
        fd.close()

    return tmp

def tmp_dir(name, create=True):
    """ Given a dir name uses the Python tempfile package to write the dir to
        the scratch directory.
    """
    dirname = os.path.basename(name)
    tmp = os.path.join(api.scratch_dir, dirname)

    if os.path.exists(tmp):
        tmp = tempfile.mktemp(prefix=dirname, dir=api.scratch_dir)

    return tmp
