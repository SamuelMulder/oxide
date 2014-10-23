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

import os, logging, logging.handlers

try:
    import config

except ImportError, err:
    print "Import config failed!\n" + str(err)
    exit()

log_file        = ".log.txt"

# Set the following in init()
log_file_fp     = None 
logs_dir        = None 
logging_level   = None 
verbosity_level = None 
console_handle  = None
file_handle     = None
max_log_size    = None
num_log_files   = None

def set_level(ltype, level):
    ltype = ltype.strip().lower()
    if ltype != "verbosity" and ltype != "logging": 
        logging.warn("Attempt to set logging with invalid type " + str(ltype))
    
    # If a string is passed in try to convert it
    if type(level) == str:
        if level.isdigit():
            level = int(level)
            
        elif level.isalpha():
            level = level.upper()
            level = logging.getLevelName(level)
            
        else:
            logging.warn("Attempt to set %s with invalid level %s ", ltype, level)
            return False
            
    if type(level) != int or level < 0 or level > 100:
        logging.warn("Attempt to set %s with invalid level %s", ltype, level)
        return False
                
    return set_level(ltype, level)
    

def set_level(ltype, level):
    logging.info("Setting %s level to %s", ltype, level)
    if ltype == "verbosity":
        global verbosity_level
        verbosity_level = level
        console_handle.setLevel(verbosity_level)
    
    elif type == "logging":
        global logging_level
        logging_level = level 
        file_handle.setLevel(logging_level)
        
    set_root_to_lowest_level()
    return True

def set_root_to_lowest_level():
    # Set the root logging to the lower level between logging and verbosity
    if verbosity_level < logging_level:
        logging.root.setLevel(verbosity_level)
    else:
        logging.root.setLevel(logging_level)

def init():
    
    global logs_dir
    logs_dir = config.dir_logs
    if not os.path.isdir(logs_dir):
        os.mkdir(logs_dir)
    
    global log_file_fp
    log_file_fp = os.path.join(logs_dir,log_file)
    
    global logging_level
    logging_level = config.logging_level
    
    global verbosity_level
    verbosity_level = config.verbosity_level
   
    set_root_to_lowest_level()

    # Remove default handler
    if len(logging.root.handlers) != 0:
        logging.root.removeHandler(logging.root.handlers[0]) 
    
    # Set up conole handler
    global console_handle
    console_handle = logging.StreamHandler()
    console_handle.setLevel(verbosity_level)
    cformatter = logging.Formatter('  * %(name)s.%(levelname)s.%(lineno)s: %(message)s')
    console_handle.setFormatter(cformatter)
    logging.root.addHandler(console_handle)
    
    # Set up file handlers
    global file_handle
    global max_log_size
    global num_log_files 
    max_log_size = int(config.logging_max_log_size) * (1024*1024)
    num_log_files = int(config.logging_num_log_files)
    if config.logging_rotate:
        file_handle = logging.handlers.RotatingFileHandler(
                    log_file_fp, maxBytes=5242880, backupCount=num_log_files)
    else:
        file_handle = logging.FileHandler(log_file_fp)
    file_handle.setLevel(logging_level)
    fformatter = logging.Formatter('%(asctime)s %(levelname)-5s %(name)s:%(lineno)-4s %(message)s')
    file_handle.setFormatter(fformatter)
    logging.root.addHandler(file_handle)
    
    
init()
