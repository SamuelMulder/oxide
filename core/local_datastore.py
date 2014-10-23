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

import os, logging
import config, sys_utils

name = "localstore"
logger = logging.getLogger(name)

localstore_dir = config.dir_localstore
sys_utils.assert_dir_exists(localstore_dir)

def local_store(plugin_name, data_name, data):
    plugin_dir = os.path.join(localstore_dir, plugin_name)
    sys_utils.assert_dir_exists(plugin_dir)
    filename = os.path.join(plugin_dir, data_name)
    logger.debug("Storing data at %s", filename)
    if not sys_utils.write_object_to_file(filename, data):
        logger.error("Not able to store data at %s", filename)
        return False
    return True

def local_exists(plugin_name, data_name):
    plugin_dir = os.path.join(localstore_dir, plugin_name)
    if not os.path.isdir(plugin_dir):
        return False
    filename = os.path.join(plugin_dir, data_name)
    logger.debug("Determining if data exists at %s", filename)
    if os.path.isdir(filename):
        logger.warn("File exists as a directory!!! %s", filename)
        return False
    return os.path.isfile(filename)
    
def local_retrieve(plugin_name, data_name):
    plugin_dir = os.path.join(localstore_dir, plugin_name)
    if not local_exists(plugin_name, data_name):
        return None

    filename = os.path.join(plugin_dir, data_name)
    data = sys_utils.read_object_from_file(filename)
    if data == None:
        logger.error("Not able to retrieve data at %s", filename)
        return None
    return data

def local_retrieve_recent(plugin_name):
    plugin_dir = os.path.join(localstore_dir, plugin_name)

    plugin_dir = os.path.join(localstore_dir, plugin_name)
    files = sys_utils.get_files_from_directory(plugin_dir)

    best = (None,0)
    for f in files:
        if os.path.getmtime(f) > best[1]:
            best = (f, os.path.getmtime(f))

    data = sys_utils.read_object_from_file(best[0])
    if data == None:
        logger.error("Not able to retrieve data at %s", filename)
        return None
    return data

def local_available_data(plugin_name):
    plugin_dir = os.path.join(localstore_dir, plugin_name)
    files = sys_utils.get_files_from_directory(plugin_dir)
    data_names = []
    if not files:
        return data_names
    for f in files:
        data_names.append(f)
    return data_names

def local_retrieve_all(plugin_name):
    plugin_dir = os.path.join(localstore_dir, plugin_name)
    files = sys_utils.get_files_from_directory(plugin_dir)
    results = {}
    if not files:
        return results

    for f in files:
        data = sys_utils.read_object_from_file(f)
        data_name = os.path.basename(f)
        results[data_name] = data

    return results

def local_count_records(plugin_name):
    plugin_dir = os.path.join(localstore_dir, plugin_name)
    if not os.path.isdir(plugin_dir):
        return 0
    logger.debug("Determining number of items in %s", plugin_dir)
    return len(os.listdir(plugin_dir))

def local_delete_function_data(plugin_name):
    # Remove all stored data for a given module
    files = retrieve_all_names(plugin_name)
    if not files:
        return True
    for fname in files:
        fullpath = os.path.join(localstore_dir, plugin_name, fname)
        sys_utils.delete_file(fullpath)
    return True
        
def local_delete_data(plugin_name, data_name):
    # Given an oid and the name of a module, remove the data for that
    #    combination if it exists.
    files = retrieve_all_names(plugin_name)
    if not files:
        return True
    for fname in files:
        fullpath = os.path.join(localstore_dir, plugin_name, fname)
        sys_utils.delete_file(fullpath)
    return True
