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
A Wizard for assisting in the loading of plugins
"""

import Tkinter as tk
import ttk
import oshell
from glob import glob
import os

class plugin_gui(tk.Tk):
    def __init__(self,master=None):
        tk.Tk.__init__(self)
        self.master = master
        self.title('Plugin Loader')
        self.result = None

        # Create frames to hold checkbuttons and control buttons
        self.frames = ttk.Frame(self)
        self.buttons = ttk.Frame(self) # error in this-> , background='white')
        self.frames.pack(expand=True, fill='both', side='top')
        self.buttons.pack(expand=True, fill='both', side='bottom')

        # Create frames for the plugin and plugin_dev checkboxes and a frame to hold them
        self.frames.plugin = ttk.Frame(self, relief='groove', width=150)
        self.frames.plugin_dev = ttk.Frame(self, relief='groove', width=150)
        self.frames.plugin.pack(expand=True, fill='both', side='left',
            padx=5, pady=5)
        self.frames.plugin_dev.pack(expand=True, fill='both', side='left',
            padx=5, pady=5)
        self.populate_plugin_checkboxes(self.frames.plugin)
        self.frames.plugin_dev.load = ttk.Button(self.frames.plugin_dev,
            text='Load Dev Plugins', command=self.populate_dev_plugin_checkboxes)
        self.frames.plugin_dev.load.pack(anchor='n', padx=10, pady=2)


        # Create the control buttons
        self.buttons.bail = ttk.Button(self.buttons, text="cancel", command=self.done);
        self.buttons.bail.pack(anchor="center", side="right", padx=10)
        self.buttons.load = ttk.Button(self.buttons, text="load", command=self.load_plugins);
        self.buttons.load.pack(anchor="center", side="right", padx=10)

        # Enter a local event loop 
        self.wait_window(self)

    def populate_plugin_checkboxes(self,master):
        self.plugin_boxes = {}
        self.plugin_var = {}
        files = glob(os.path.join("plugins", "*.py"))
        files = [ os.path.split(file)[1].replace(".py", "")
                   for file in files if not "__init__" in file ]
        for p in files:
            self.plugin_var[p] = tk.IntVar()
            self.plugin_boxes[p] = tk.Checkbutton(master, text=p, variable=self.plugin_var[p])
            self.plugin_boxes[p].pack(expand=True, fill='x', side='top', anchor='w',
                padx=5, pady=2)
            if p in oshell.instance.plugins.keys():  # oshell.plugin_list:
                self.plugin_boxes[p].select()
            else:
                self.plugin_boxes[p].deselect()

    def populate_dev_plugin_checkboxes(self):
        self.dev_plugin_boxes = {}
        self.frames.plugin_dev.load.pack_forget()
        files = glob(os.path.join("plugins_dev", "*.py"))
        files = [ os.path.split(file)[1].replace(".py", "")
                   for file in files if not "__init__" in file ]
        for p in files:
            self.dev_plugin_boxes[p] = tk.Checkbutton(self.frames.plugin_dev, text=p)
            self.dev_plugin_boxes[p].pack(expand=True, fill='x', side='top',
                anchor='w', padx=5, pady=2)
            if p in oshell.instance.plugins.keys():  # oshell.plugin_list:
                self.dev_plugin_boxes[p].select()
            else:
                self.dev_plugin_boxes[p].deselect()
    
    def done(self):
        self.destroy()
        exit()

    def load_plugins(self):
        line = ""
        for plugin in self.plugin_boxes.keys():
            if self.plugin_var[plugin].get():
                line += plugin + " "
        print "Plugins checked: ", line
        oshell.instance.do_plugin(line)
        self.destroy()



def run_plugin_gui():
    gui = plugin_gui()
    gui.mainloop()

