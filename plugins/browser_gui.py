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
TODO:
    Add a display of number of oids in a collection next to the collection name

    Add the displaying of 'tags' to the metadata

    Use the type_filter function to display how many files of a given type are
        in the currently selected collection
            type_filter &sample --type=PE | count

    Allow the selection of multiple files to add to a collection.
        (maybe a seperate frame for this?)
        maybe also the ability to create collections?

    Add histogram counts for:
        byte_ngrams
        opcode_ngrams

    Have the hex view written to a file, instead of calculated on the fly
        will require creating a plug_in for reading and writing the 
        hexlified and asciified strings to the local data store.

        api.local_store(plug_in_name, oid, {'hexlified':hex_str, 'asciified':ascii_str})
        api.local_retrieve(plug_in_name, oid, {'hexlified':hex_str, 'asciified':ascii_str})

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

class BrowseView(tk.Tk):
    def __init__(self, master=None):
        tk.Tk.__init__(self)
        self.master = master
        self.title('Oxide Browser')
        self.browse_frame = BrowseFrame(self)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.browse_frame.grid (column=0, row=0, sticky='nsew')

class BrowseFrame(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.threads = {}
        self.current_index = -1
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
        self.collection_box.selection_set(0)
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
        self.metadata_display['width'] = 60
        self.metadata_display['height'] = 5
        self.metadata_display['borderwidth'] = 4
        self.metadata_display['font'] = 'TkFixedFont'
        # OptionMenu to select how to display the file
        self.options = ['hex           ',
                        'header        ',
                        'imports       ',
                        'byte histogram',
                        'opcode histogram']

        self.file_display_type_str = tk.StringVar(master=self)
        self.file_display_type_str.set(self.options[0])
        self.file_display_option_menu = ttk.OptionMenu(self, 
                       self.file_display_type_str, self.options[1], 
                       command=self.on_file_data_select, *self.options)
        self.file_display_option_menu.grid(column=4, row=1)

        # Display to contain the files attributes
        self.file_display = ScrolledText.ScrolledText(master=self)
        self.file_display.grid(column=4, row=2, sticky='nsew', columnspan=3)
        self.file_display['width'] = 90
        self.file_display['height'] = 10
        self.file_display['borderwidth'] = 4
        self.file_display['font'] = 'TkFixedFont'
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
        
        self.on_collection_select()

    def on_collection_select(self, event=None):
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
            print "Index Error: no collection selected"

    def display_filenames(self, oid):
        file_names = list(api.get_names_from_oid(oid))
        file_name = ', '.join(file_names)
        self.file_name_box.insert(tk.END, file_name)
        if self.file_count.get():
            self.file_count.set(int(self.file_count.get())+1)

    def on_file_name_select(self, event):
        try:
            index = int(self.file_name_box.curselection()[0])
            self.current_index = index
            fnames = self.file_name_box.get(index)
            oid = self.oids[index]
            self.display_file_data(oid,fnames)
        except IndexError:
            print "Index Error: no filename selected"
            
    def on_file_data_select(self, event):
        try:
            if self.current_index == -1:
                return
            index = self.current_index
            fnames = self.file_name_box.get(index)
            oid = self.oids[index]
            self.display_file_data(oid,fnames)
        except IndexError:
            print "Index Error: cannot process data, no filename selected"
            

    def display_file_data(self, oid, fnames):
        data_list = []
        self.file_display.delete(index1='1.0', index2=tk.END)
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
        display_option = self.file_display_type_str.get()
        if display_option ==   'hex           ':
            data_list = self.build_hex_str(oid)
        elif display_option == 'header        ':
            data_list = self.build_header_string(oid)
        elif display_option == 'imports       ':
            data_list = self.build_imports_string(oid)
        elif display_option == 'byte histogram':
            data_list = self.build_hist_string('byte_histogram', oid)
        elif display_option == 'opcode histogram':
            data_list = self.build_hist_string('opcode_histogram', oid)
        for line in data_list:
            self.file_display.insert(index=tk.END, chars=line+ "\n")

    def build_hex_str(self, oid):  
        data = api.get_field('files', oid, 'data')
        str_list = []
        address = 0
        line_width = 16
        while data:
            hex_bytes = []
            ascii_bytes = []
            line, data = data[:line_width], data[line_width:]
            for i, byte in enumerate(line):
                hex_bytes.append(hexlify(byte) + ' ')
                if ord(byte) >= 32 and ord(byte) <= 126:
                    ascii_bytes.append(byte)
                else:
                    ascii_bytes.append('.')
                if i == 7: 
                    ascii_bytes.append('  ')
                    hex_bytes.append('  ')
            formatted_line = '%08d    %-50s  %s' % (address, 
                             ''.join(hex_bytes), ''.join(ascii_bytes))
            str_list.append(formatted_line)
            address += line_width
        return str_list

    def build_header_string(self, oid):
        header = api.get_field("object_header", oid, "header")
        if not header:
            return ["N/A"]
        str_list = []
        addr_size = "32 bit"
        if header.is_64bit():
            addr_size = "64 bit"
        entry_string = ""
        for e in header.get_entries():
            entry_string += "%s (%s)  " % (hex(e), (e))
        str_list.append("  - Addr Size:      %s"      % (addr_size))
        str_list.append("  - Image Base:     %s (%s)" % (hex(header.image_base), header.image_base))
        str_list.append("  - Image Size:     %s "     % (header.image_size)) 
        str_list.append("  - Code Size:      %s "     % (header.code_size))
        str_list.append("  - Code Base:      %s (%s)" % (hex(header.code_base), header.code_base))
        str_list.append("  - Data Base:      %s (%s)" % (hex(header.data_base), header.data_base))  
        str_list.append("  - File Alignment: %s"      % (header.file_alignment))
        str_list.append("  - Image Version:  %s"      % (header.image_version))
        str_list.append("  - Linker Version: %s"      % (header.linker_version))
        str_list.append("  - OS Version:     %s"      % (header.os_version))
        str_list.append("  - Entry points:   %s"      % (entry_string))
        str_list.append("--------------------------")      
        str_list.append(" - Number of Sections: %s  " % (len(header.section_info)) )
        secs = header.section_info
        offsets = [secs[s]["section_offset"] for s in secs]
        offsets.sort()
        for o in offsets:
            for s in secs:
                if secs[s]['section_offset'] == o:
                    str_list.append("   - Section %s           "      % (str(s).rstrip("\00")))
                    str_list.append("     - Exec?            %s"      % (str(secs[s]['section_exec'])))
                    str_list.append("     - Start offset:    %s (%s)" % (hex(secs[s]['section_offset']), secs[s]['section_offset']))
                    str_list.append("     - Start RVA:       %s (%s)" % (hex(secs[s]['section_addr']), secs[s]['section_addr'])) 
                    str_list.append("     - Section Length:  %s (%s)" % (hex(secs[s]['section_len']), secs[s]['section_len']))
        return str_list

    def build_imports_string(self, oid):        
        header = api.get_field("object_header", oid, "header")
        t = api.get_field("src_type", oid, "type")
        if not header:
            return ["N/A"]
        str_list = []
        str_list.append("Import Address Table :" )
        if not header.imports:
            str_list.append("    + No import table")
        else:
            entries = header.imports.keys()
            entries.sort()
            for entry in entries:
                if t == "MACHO":
                    str_list.append("    - Lib: " + entry)
                    names = header.imports[entry].keys()
                    names.sort()
                    for name in names:
                        value = header.imports[entry][name]["n_value"]
                        str_list.append("      - %s   :   %s (%s)" % ( name, hex(value), value))
                elif t == "ELF":
                    str_list.append("    - Lib: " + entry)
                    names = header.imports[entry].keys()
                    names.sort()
                    for name in names:
                        value = header.imports[entry][name]["value"]
                        str_list.append("      - %s   :   %s (%s)" % ( name, hex(value), value))
                elif t == "PE":
                    str_list.append("    - DLL: " + entry)
                    if header.imports[entry]["addresses"]:                
                        for imp in header.imports[entry]["addresses"]:
                            str_list.append("      - %s   :   %s"%(header.imports[entry]["addresses"][imp], imp))
        return str_list

    def build_hist_string(self, mod_name, oid, cutoff=200):
        str_list = []
        args = (mod_name, oid)
        if api.exists(mod_name=mod_name, oid=oid):
            hist = api.retrieve(mod_name=mod_name,oid_list=[oid,])
            hist_items = hist.items()
            hist_items.sort(key=operator.itemgetter(1), reverse=True)
            hist_items = hist_items[:cutoff]
            if len(hist) == 0:
                str_list.append("No keys were found.")
            for key, value in hist_items:
                if mod_name == "byte_histogram":
                    formatted_pair = '%s\t%8d' % (hexlify(key),value)
                else:
                    formatted_pair = '%s\t%8d' % (key,value)
                str_list.append(formatted_pair)
        else:
            if self.threads.has_key(args) and not self.threads[args].is_alive(): # Requested and returned NULL.
                str_list.append("N/A")
            else:
                str_list.append("%s file does not exist for:" % mod_name)
                str_list.append("\t%s" % oid)
                if self.threads.has_key(args) and self.threads[args].is_alive(): # Requested and still waiting.
                    str_list.append("It is still being created.")
                else:    # First time this has been requested.
                    str_list.append("It is being created.")
                    creation_thread = threading.Thread(target=api.process, args=args)
                    creation_thread.start()
                    self.threads[args] = creation_thread
        return str_list

def run_browser_gui(args, opts):
    """ Plugin: starts the browser GUI. Oxide processing is suspendended until
                the browser GUI is dismissed.
        syntax: run_browser_gui
    """
    app=BrowseView()
    app.mainloop()
    
def browser_wrapper():
    run_browser_gui([],{})

def launch_browser_gui(args, opts):
    """ Plugin: starts the browser GUI as a separate thread, allowing oxide
                shell processing to continue
        syntax: launch_browser_gui
    """
    t = threading.Thread(target=browser_wrapper)
    t.start()


exports = [run_browser_gui, launch_browser_gui]

if __name__ == '__main__':
    run_browser_gui(None,None)
