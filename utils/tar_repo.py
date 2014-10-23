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

"""
Clones HEAD in the repository and makes a tarball of the resulting
file. Use this to copy the repository to other users/networks.
"""
import datetime, os, shutil, _path_magic
import core.config as config

now = datetime.datetime.now()
dstamp = datetime.datetime.strftime(now,"%Y_%m-%d")
repo_fname = "oxide-" + dstamp + ".tar.bz2" 

clone_dir = os.path.join(config.dir_scratch, "oxide")
if os.path.isdir(clone_dir):
    print "Clone dir already exists - removing"
    shutil.rmtree(clone_dir)
    
cmd = 'git clone ' + config.dir_root + " " + clone_dir
os.system(cmd)

os.chdir(config.dir_scratch)
if os.path.isfile(repo_fname):
    print "Tar file already exists - removing"
    os.remove(os.path.join(config.dir_root, repo_fname))

c = raw_input("When you are finished making manual changes to the repo, press return.")

print "Tar and compressing cloned repo to", repo_fname
cmd = 'tar cfj ' + repo_fname + ' oxide/*' 
os.system(cmd)

print "Moving tar file to current directory"
shutil.move(repo_fname, config.dir_root)

print "Cleaning up cloned repo"
shutil.rmtree(clone_dir)
print "Done."
