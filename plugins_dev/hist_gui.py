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

import core.oxide
import api
import Tkinter as tk
import ttk
import ScrolledText
from binascii import hexlify
import os.path
import threading
import operator
import matplotlib as mpl
mpl.use('TkAgg')
import pylab
import numpy

class HistView(tk.Tk):
    def __init__(self, master=None):
        tk.Tk.__init__(self)
        self.master = master
        self.title('Oxide Browser')
        self.histogram_frame = HistFrame(self)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.histogram_frame.grid (column=0, row=0, sticky='nsew')
        # set the 'x' button to kill the capture thread when the window closes
        self.protocol('WM_DELETE_WINDOW', self._quit)

    def _quit(self):
        self.histogram_frame.clean_quit()
        self.quit()    # stops mainloop
        self.destroy()

class HistFrame(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # Have the columns all grow evenly when the window is resized.
        self.columnconfigure(0, weight=0, minsize=20)
        self.columnconfigure(1, weight=0, minsize=20)
        self.columnconfigure(2, weight=0, minsize=20)
        self.columnconfigure(3, weight=0, minsize=20)
        self.columnconfigure(4, weight=1, minsize=20)
        self.columnconfigure(5, weight=1, minsize=20)
        self.columnconfigure(6, weight=1, minsize=20)
        self.rowconfigure(0, weight=0,  minsize=20)
        self.rowconfigure(1, weight=0,  minsize=10)
        self.rowconfigure(2, weight=10, minsize=20)
        self.rowconfigure(3, weight=0,  minsize=20)
        # Listbox to contain the collection names
        self.collection_frame = ttk.Frame(master=self)
        self.collection_frame['padding'] = 5
        self.collection_frame.grid(column=0, row=0, sticky='nsew', 
                                   columnspan=2, rowspan=3)
        self.collection_scroll = ttk.Scrollbar(self.collection_frame)
        self.collection_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.collection_box = tk.Listbox(self.collection_frame)
        self.collection_box['width'] = 30
        self.collection_box['height'] = 60
        self.collection_box['font'] = 'TkFixedFont'
        self.collection_box['borderwidth'] = 0
        self.collection_box['highlightthickness'] = 0
        self.collection_box.bind('<<ListboxSelect>>', self.on_collection_select)
        self.collection_box.pack(fill=tk.BOTH, expand=1)
        self.collection_box.configure(yscrollcommand=self.collection_scroll.set)
        self.collection_scroll.configure(command=self.collection_box.yview)
        self.collection_names = api.collection_names()
        for collection_name in self.collection_names:
            self.collection_box.insert(tk.END, collection_name)
        # Listbox to contain each file name in the selected collection
        self.file_name_frame = ttk.Frame(master=self)
        self.file_name_frame['padding'] = 5
        self.file_name_frame.grid(column=2, row=0, sticky='nsew', 
                                   columnspan=2, rowspan=3)
        self.file_name_scroll = ttk.Scrollbar(self.file_name_frame)
        self.file_name_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_name_box = tk.Listbox(self.file_name_frame)
        self.file_name_box['width'] = 30
        self.file_name_box['height'] = 20
        self.file_name_box['font'] = 'TkFixedFont'
        self.file_name_box['borderwidth'] = 0
        self.file_name_box['highlightthickness'] = 0
        self.file_name_box.pack(fill=tk.BOTH, expand=1)
        self.file_name_box.bind('<<ListboxSelect>>', self.on_file_name_select)
        self.file_name_box.configure(yscrollcommand=self.file_name_scroll.set)
        self.file_name_scroll.configure(command=self.file_name_box.yview)

        # Display to contain the files attributes
        self.metadata_display = tk.Text(master=self)
        self.metadata_display.grid(column=4, row=0, sticky='nsew', columnspan=3)
        self.metadata_display['width'] = 200
        self.metadata_display['height'] = 5
        self.metadata_display['borderwidth'] = 4
        self.metadata_display['font'] = 'TkFixedFont'

        # OptionMenu to select how to display the file
        self.options = ['              ',
                        'byte histogram',
                        'opcode histogram']
        self.file_display_type_str = tk.StringVar(master=self)
        self.file_display_type_str.set(self.options[0])
        self.file_display_option_menu = ttk.OptionMenu(self, 
                       self.file_display_type_str, self.options[0], 
                       command=self.on_file_data_select, *self.options)
        self.file_display_option_menu.grid(column=4, row=1)

        # Create a display to contain the histogram image
        self.display = tk.Frame(master=self)
        self.display.grid(column=4, row=2, sticky='nsew',
                          columnspan=3)
        self.display['width'] = 40
        self.display['height'] = 40
        self.display['borderwidth'] = 2

        # Label for the file counter
        self.label_str = tk.StringVar()
        self.label_str.set('')
        self.count_label = ttk.Label(self, textvariable=self.label_str)
        self.count_label.grid(column=2, row=3, sticky='nse')
        # File counter
        self.file_count = tk.StringVar()
        self.file_count.set('')
        self.file_count_display = ttk.Label(self, textvariable=self.file_count)
        self.file_count_display.grid(column=3, row=3, sticky='nsw')
        # give every widget in the mainframe a little padding
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def sel(self):
        '''
        Action taken by the radio button selection
        '''
        self.selection = self.selection_var.get()
        print self.selection
        self.display_hist()

    def on_collection_select(self, event):
        try:
            index = int(self.collection_box.curselection()[0])
            self.current_collection = self.collection_box.get(index)
            self.file_name_box.delete(first=0, last=tk.END)
            collection_id = api.get_cid_from_name(self.current_collection)
            collection_features = api.retrieve('collections', collection_id)
            self.oids = collection_features['oid_list']
            self.label_str.set('Loading: ')
            self.file_count.set(0)
            for oid in self.oids:
                self.after(0, self.display_filenames, oid)
            self.file_count.set('')
            self.label_str.set('')
        except IndexError:
            print "Index Error..."

    def display_filenames(self, oid):
        file_names = list(api.get_names_from_oid(oid))
        file_name = ', '.join(file_names)
        self.file_name_box.insert(tk.END, file_name)
        if self.file_count.get():
            self.file_count.set(int(self.file_count.get())+1)

    def on_file_name_select(self, event):
        try:
            index = int(self.file_name_box.curselection()[0])
            fnames = self.file_name_box.get(index)
            oid = self.oids[index]
            self.display_file_data(oid,fnames)
        except IndexError:
            print "Index Error..."
            
    def on_file_data_select(self, event):
        try:
            index = int(self.file_name_box.curselection()[0])
            fnames = self.file_name_box.get(index)
            oid = self.oids[index]
            self.display_file_data(oid,fnames)
        except IndexError:
            print "Index Error..."

    def display_file_data(self, oid, fnames):
        meta = api.retrieve('file_meta', oid)
        size = meta['size']
        if size > 1000000000:
            formatted_size = "(%dG)" % (size / 1000000000) 
        elif size > 1000000:
            formatted_size = "(%dM)" % (size / 1000000) 
        elif size > 1000:
            formatted_size = "(%dK)" % (size / 1000)
        else:
            formatted_size = ''
        file_type = api.get_field("src_type", oid, 'type')
        file_description = "File Names: " + fnames + '\n'
        file_description += "Size: %7d %s\n" % (size, formatted_size)
        file_description +=  "File Type: " + file_type + '\n'
        file_description +=  "Oxide ID: " + oid + '\n'
        self.metadata_display.delete(index1='1.0', index2=tk.END)
        self.metadata_display.insert(index='1.0', chars=file_description)

        # calculate and display the histogram
        display_option = self.file_display_type_str.get()
        if display_option ==   '              ':
            self.clear()
            return
        elif display_option == 'byte histogram':
            hist = self.get_byte_hist(oid)
        elif display_option == 'opcode histogram':
            hist = self.get_opcode_hist(oid, cutoff=20)
        self.display_hist(hist)

    def display_hist(self, freq):
        self.clear()
        data = sorted(freq.items())
        if len(data) == 0:
            data = [('\x00',0),]
        x, y = zip(*data)
        xlocs = numpy.arange(len(x))
        fig = pylab.figure("hist_fig")
        self.ax = fig.gca()
        self.ax.bar(xlocs + 0.6, y)
        self.ax.set_xticks(xlocs + 1)
        self.ax.set_xticklabels(x[:])
        self.ax.set_xlim(0.0, xlocs.max() + 2)
        for tick in self.ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(6)
            tick.label.set_rotation('vertical')
        fig.add_axes(self.ax)
        if not hasattr(self, 'canvas'):
            self.canvas = mpl.backends.backend_tkagg.FigureCanvasTkAgg(fig, 
                                                    master=self.display)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.show()

    def get_opcode_hist(self, oid, cutoff=20):
        if api.exists('opcode_histogram', oid):
            hist = api.retrieve('opcode_histogram',oid_list=[oid,])
            hist_items = hist.items()
            hist_items.sort(key=operator.itemgetter(1), reverse=True)
            hist_items = hist_items[:cutoff]
            hist = dict(hist_items)
        else:
            print "opcode_histogram file does not exist for:",
            print "%s" % oid
            args = ('opcode_histogram', oid)
            if self.threads.has_key(args):
                print "It is still being created."
            else:
                print "It is being created."
                creation_thread = threading.Thread(target=api.process, args=args)
                creation_thread.start()
            hist = {}
        return hist

    def get_byte_hist(self,oid):
        if api.exists('byte_histogram', oid):
            byte_hist = api.retrieve('byte_histogram',oid_list=[oid,])
            # convert all of the keys into printable form
            hexlified_hist = {}
            for key, value in byte_hist.items():
                hexlified_hist[hexlify(key)] = value
            # add in 0s for the values that are not currently in the hist
            for i in range(0xff):
                if hex(i)[2:] not in hexlified_hist:
                    hexlified_hist[hex(i)[2:]] = 0
            hist = hexlified_hist
        else:
            print "byte_histogram file does not exist for:",
            print "%s" % oid
            args = ('byte_histogram', oid)
            if self.threads.has_key(args):
                print "It is still being created."
            else:
                print "It is being created."
                creation_thread = threading.Thread(target=api.process, args=args)
                creation_thread.start()
            hist = {}
        return hist

    def clear(self):
        if hasattr(self, 'canvas') and hasattr(self,'ax'):
            self.ax.clear()

    def clean_quit(self):
        self.destroy() # this is necessary on Windows to prevent
                       # Fatal Python Error: PyEval_RestoreThread: NULL tstate

def run_hist_gui(args,opts):
    app=HistView()
    app.mainloop()
    
exports = [run_hist_gui]

if __name__ == '__main__':
    run_hist_gui(None, None)
