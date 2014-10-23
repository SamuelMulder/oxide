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

import logging, xmlrpclib, socket, time, os
import oshell , client, sys_utils, progress, config
from oshell import error_handler
from oshell import ShellSyntaxError
import oxide as loc_oxide
name = "rshell"
logger = logging.getLogger(name)

class oxide_proxy:
    def __init__(self, ros):
        # Wrap the proxy methods with the decode method
        methods = ros.proxy.system.listMethods()
        for m in methods:
            if m == "import_file":
                setattr(self, m, client.decode_file(getattr(ros.proxy, m)))
            else:
                setattr(self, m, client.decode(getattr(ros.proxy, m)))
        self.scratch_dir = loc_oxide.api.scratch_dir
        self.import_file = ros.import_file
        
            
class RemoteOxideShell(oshell.OxideShell):
    def __init__(self, server_ip, server_port):
        try:
            self.proxy = client.get_proxy(server_ip, server_port)
            self.oxide = oxide_proxy(self)
            oshell.OxideShell.__init__(self)
            self.scratch_dir = loc_oxide.api.scratch_dir
            
        except socket.error:
            print "ERROR: Unable to connect!"
            exit()
        
    
    def postcmd(self, stop, line):
        """ Overwrite this method because this method checks vars that do
            not exist locally
        """
        return self.stop
            
    def import_file(self, file_location):
        """ Process the file locally - only transmit if it does not exist remotely
            1. Get the oid and metadata
            2. Check if the file exist remotely: 
               a. If the file does not exist remotely - transmit the file
               b. If the file does exist remotely - don't transmit the file
        """
        new_file = False
        fd = sys_utils.import_file(file_location, config.file_max)
        if not fd:
            return None, False
        oid = loc_oxide.get_oid_from_data(fd["data"])
        if not oid:
            logger.error("Not able to get and oid for %s", file_location)
            return None, False 
        
        opts_file = { "file_contents":fd["data"]}   
        opts_meta = { "file_location":file_location, "stat":fd["file_stat"]}   
        
        if not self.oxide.exists("files", oid, {}):
            new_file = True
            if not self.oxide.process("files", oid, opts_file):
                logger.error("Not able to process file data %s",file_location)
                return None, False
        
        if not self.oxide.process("file_meta", oid, opts_meta, True):
            logger.error("Not able to process file metadata %s",file_location)
            return None, False

        logger.debug("%s file import complete.", file_location)
        return oid, new_file
        
                
    def import_files(self, args, opts): # import <file> | <dir> ...
        """ Overrite this method so that files/directories are processed locally
        """
        oid_list = []
        total_new = 0
        for arg in args:
            if os.path.isfile(arg): # Import a file
                oid, new_file = self.import_file(arg) # Call local file import 
                if not oid:
                    print "  - Not able to import file %s" % (arg) 
                    continue
                oid_list.append(oid)
                total_new += new_file
            elif os.path.isdir(arg): # Import a directory
                oids, new_files = self.import_directory(arg) # Call local dir import
                if not oids:
                    print "  - Not able to import diretory %s" % (arg) 
                    continue
                oid_list.extend(oids)
                total_new += new_files
            else:
                print "  - %s is not a file or directory, skipping" % (arg)
        if not oid_list:
            print "  - No files were imported"
        else:
            print "  - %s files imported, %s are new" % (len(oid_list), total_new)
        
        return oid_list


    def import_directory(self, directory):
        """ Process the local directory calling the local import on each file
        """
        files_list = sys_utils.get_files_from_directory(directory)
        if files_list == None:
            return None, 0
        oids = []
        num_new_files = 0
        p = progress.progress(len(files_list))
        for file_location in files_list:
            oid, new_file = self.import_file(file_location)
            p.tick()
            if oid:
                oids.append(oid)
                if new_file:
                    num_new_files += 1
        oids = list(set(oids)) # assert uniqueness 
        return oids, num_new_files
 