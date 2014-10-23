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
    Add the ability to save user comments

    Add some type of progress indicator.... big files look like hangs

    Move OidSelectDialog to its own module

    Make columns resizable

    Try combining the Feature and Auto Annotation columns
"""

import core.oxide
import api
import re_lib
import Tkinter as tk
import ttk
import ScrolledText
from binascii import hexlify
import os.path
import threading
import operator
from collections import defaultdict 
import os

class FileView(tk.Tk):
    def __init__(self, master=None):
        self.oid = None
        tk.Tk.__init__(self)
        self.master = master
        self.title('File Viewer')
        self.view_frame = FileViewFrame(self)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.view_frame.grid(column=0, row=0, sticky='nsew')

class FileViewFrame(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.master = master

        # Have the columns remain fixed when the window is resized.
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=0)
        self.columnconfigure(5, weight=0)
        self.columnconfigure(6, weight=0)

        # Have the window row grow when the window is resized.
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # Label for the offset display
        self.offset_label = ttk.Label(master=self, text='Offset (RVA)')
        self.offset_label.grid(column=0, row=0)

        # Display to contain the offsets
        self.offset_display = tk.Text(master=self, wrap=tk.NONE)
        self.offset_display.grid(column=0, row=1, sticky='nsew')
        self.offset_display['width'] = 20
        self.offset_display['height'] = 50
        self.offset_display['font'] = 'TkFixedFont'

        # Label for the hex display
        self.hex_label = ttk.Label(master=self, text='Hex')
        self.hex_label.grid(column=1, row=0)

        # Display to contain the hex version of the file contents
        self.hex_display = tk.Text(master=self, wrap=tk.NONE)
        self.hex_display.grid(column=1, row=1, sticky='nsew')
        self.hex_display['width'] = 25
        self.hex_display['font'] = 'TkFixedFont'

        # Label for the ascii display
        self.ascii_label = ttk.Label(master=self, text='ASCII')
        self.ascii_label.grid(column=2, row=0)

        # Display to contain the ascii version of the file contents
        self.ascii_display = tk.Text(master=self, wrap=tk.NONE)
        self.ascii_display.grid(column=2, row=1, sticky='nsew')
        self.ascii_display['width'] = 8
        self.ascii_display['font'] = 'TkFixedFont'

        # Label for the feature display
        self.feature_label = ttk.Label(master=self, 
                             text='Feature (Opcode or Header Field)')
        self.feature_label.grid(column=3, row=0)

        # Display to contain the features (opcodes, header fields, etc)
        self.feature_display = tk.Text(master=self, wrap=tk.NONE)
        self.feature_display.grid(column=3, row=1, sticky='nsew')
        self.feature_display['width'] = 120
        self.feature_display['font'] = 'TkFixedFont'

        # Label for the auto annotation display
        self.auto_annotation_label = ttk.Label(master=self, 
                                     text='Automatically Generated Annotation')
        self.auto_annotation_label.grid(column=4, row=0)

        # Display to contain the automatically generated annotations
        self.auto_annotation_display = tk.Text(master=self, wrap=tk.NONE)
        self.auto_annotation_display.grid(column=4, row=1, sticky='nsew')
        self.auto_annotation_display['width'] = 42
        self.auto_annotation_display['font'] = 'TkFixedFont'

        # Label for the user comment display
        self.user_comment_label = ttk.Label(master=self, text='User Comment')
        self.user_comment_label.grid(column=5, row=0)

        # Display to contain the user added comments
        self.user_comment_display = tk.Text(master=self, wrap=tk.NONE)
        self.user_comment_display.grid(column=5, row=1, sticky='nsew')
        self.user_comment_display['width'] = 42
        self.user_comment_display['font'] = 'TkFixedFont'

        # Scrollbar to controll all of the displays
        self.scroll_bar = tk.Scrollbar(orient="vertical", borderwidth=1,
                                command=self.on_scrolling_bar)
        self.offset_display.configure(yscrollcommand=self.on_scrolling_text)
        self.hex_display.configure(yscrollcommand=self.on_scrolling_text)
        self.ascii_display.configure(yscrollcommand=self.on_scrolling_text)
        self.feature_display.configure(yscrollcommand=self.on_scrolling_text)
        self.auto_annotation_display.configure(yscrollcommand=self.on_scrolling_text)
        self.user_comment_display.configure(yscrollcommand=self.on_scrolling_text)
        self.scroll_bar.grid(column=6, row=0, sticky='nsew')
        

        # Button to select an oid to load from
        self.load_button = ttk.Button(self, text='Load Oxide ID')
        self.load_button['command'] = self.launch_oid_browser
        self.load_button.grid(column=2, row=2)

        #Button to apply template
        self.template_button = ttk.Button(self, text='Apply Template')
        self.template_button['command'] = self.launch_template_browser
        self.template_button.grid(column = 4,row = 2)

        # give every widget in the mainframe a little padding
        for child in self.winfo_children():
            child.grid_configure(padx=2, pady=2)

        # make text field uneditable, except for user comments field
        self.offset_display['state'] = 'disabled'
        self.hex_display['state'] = 'disabled'
        self.ascii_display['state'] = 'disabled'
        self.feature_display['state'] = 'disabled'
        self.auto_annotation_display['state'] = 'disabled'

    def on_scrolling_bar(self, *args):
        """
        Callback for when the scrollbar is used. 
        Ensures that all of the text fields scroll together, 
        when the scrollbar is used.
        """
        self.offset_display.yview(*args)
        self.hex_display.yview(*args)
        self.ascii_display.yview(*args)
        self.feature_display.yview(*args)
        self.auto_annotation_display.yview(*args)
        self.user_comment_display.yview(*args)

    def on_scrolling_text(self, *args):
        """
        Callback for when any of the text boxes are scrolled, 
        without using the scroll_bar directly. 
        Ensures that all of the text fields scroll together.
        """
        self.offset_display.yview_moveto(args[0])
        self.hex_display.yview_moveto(args[0])
        self.ascii_display.yview_moveto(args[0])
        self.feature_display.yview_moveto(args[0])
        self.auto_annotation_display.yview_moveto(args[0])
        self.user_comment_display.yview_moveto(args[0])
        self.scroll_bar.set(*args)

    def create_display_strings(self, oid):
        data = api.get_field('files', oid, 'data')
        self.offsets = []
        self.lengths = {}
        self.features = defaultdict(str)
        self.hex_strs = {}
        self.ascii_strs = {}
        self.auto_annotations = {}
        self.user_comments = {}
        
        self.header = api.get_field('object_header', oid, 'header')

        instructions = api.get_field('disassembly', oid, 'insns')
        if instructions:
            self.offsets.extend(instructions.keys())
            for offset, instruction in instructions.items():
                instruction_string = re_lib.instruction_to_string(instruction)
                if len(self.features[offset]) > 0:
                    self.features[offset] += '  ::  %s' % instruction_string
                else:
                    self.features[offset] = instruction_string
                length = instruction['len']
                self.lengths[offset] = length
                current_offset = offset
                while length > 8:
                    self.lengths[current_offset] = 8
                    current_offset +=8
                    self.offsets.append(current_offset)
                    self.features[current_offset] = ' "" '
                    length -= 8
                    self.lengths[current_offset] = length

        header_fields = api.get_field('pe_parse', oid, 'offsets')
        if header_fields:
            self.offsets.extend(header_fields.keys())
            for offset, field in header_fields.items():
                field_lengths = []
                field_strings = []
                if isinstance(field, list):
                    for element in field:
                        field_lengths.append(element['len'])
                        field_strings.append(element['string'])
                else:
                    field_lengths.append(field['len'])
                    field_strings.append(field['string'])
                field_length = min(field_lengths)
                field_string = ' :: '.join(field_strings)
                if len(self.features[offset]) > 0:
                    self.features[offset] += '  ::  %s' % field_string
                else:
                    self.features[offset] = field_string
                self.lengths[offset] = field_length
                current_offset = offset
                while field_length > 8:
                    self.lengths[current_offset] = 8
                    current_offset +=8
                    self.offsets.append(current_offset)
                    self.features[current_offset] += ' "" '
                    field_length -= 8
                    self.lengths[current_offset] = field_length

        # add an offset and feature for end-of-file
        self.offsets.append(len(data))
        self.features[len(data)] += " EOF"
        self.lengths[len(data)] = 0

        # consolidate and sort the offset list
        self.offsets = list(set(self.offsets))
        self.offsets.sort()

        # add offsets and empty features for sections without any other feature
        index = 0
        new_offsets = []
        for offset in self.offsets:
            while offset > index:
                if offset - index > 8:
                    self.lengths[index] = 8
                else:
                    self.lengths[index] = offset - index
                self.features[index] = ''
                new_offsets.append(index)
                index += self.lengths[index]
            index = offset + self.lengths[offset]
        self.offsets.extend(new_offsets)

        # consolidate and sort the offset list
        self.offsets = list(set(self.offsets))
        self.offsets.sort()

        
        # add basic auto generated features
        call_map = api.retrieve('map_calls', oid)
        
        functions = api.retrieve('function_extract', oid)
        function_offsets = {}

        if functions:
            for f in functions:
                function_offsets[self.header.get_offset(functions[f]['start'])] = "**** %s ****"%functions[f]['name']
            
        # create hex and ascii strings for each offset
        previous_offset = 0
        for offset in self.offsets:
            length = self.lengths[offset]
            self.hex_strs[offset] = self.build_hex_str(data[offset:offset+length])
            self.ascii_strs[offset] = self.build_ascii_str(data[offset:offset+length])
            if call_map and offset in call_map['internal_functions']:
                self.auto_annotations[offset] = call_map['internal_functions'][offset]
            elif call_map and offset in call_map['system_calls']:
                self.auto_annotations[offset] = call_map['system_calls'][offset]
            elif offset in function_offsets:
                self.auto_annotations[offset] = function_offsets[offset]
            else:
                self.auto_annotations[offset] = ""
            self.user_comments[offset] = ""

    def build_hex_str(self, line):
        hex_bytes = []
        for byte in line:
            hex_bytes.append(hexlify(byte) + ' ')
        return ''.join(hex_bytes)

    def build_ascii_str(self, line):
        ascii_bytes = []
        for byte in line:
            if ord(byte) >= 32 and ord(byte) <= 126:
                ascii_bytes.append(byte)
            else:
                ascii_bytes.append('.')
        return ''.join(ascii_bytes)

    def clear_displays(self):
        self.offset_display['state'] = 'normal'
        self.hex_display['state'] = 'normal'
        self.ascii_display['state'] = 'normal'
        self.feature_display['state'] = 'normal'
        self.auto_annotation_display['state'] = 'normal'
        self.offset_display.delete(1.0, tk.END)
        self.hex_display.delete(1.0, tk.END)
        self.ascii_display.delete(1.0, tk.END)
        self.feature_display.delete(1.0, tk.END)
        self.auto_annotation_display.delete(1.0, tk.END)
        self.user_comment_display.delete(1.0, tk.END)
        self.offset_display['state'] = 'disabled'
        self.hex_display['state'] = 'disabled'
        self.ascii_display['state'] = 'disabled'
        self.feature_display['state'] = 'disabled'
        self.auto_annotation_display['state'] = 'disabled'

    def display_file_data(self, oid):
        self.offset_display['state'] = 'normal'
        self.hex_display['state'] = 'normal'
        self.ascii_display['state'] = 'normal'
        self.feature_display['state'] = 'normal'
        self.auto_annotation_display['state'] = 'normal'
        for offset in self.offsets:
            if self.header and self.header.get_rva(offset):
                self.offset_display.insert(index=tk.END, chars='%08x (%08x)\n' % (offset, self.header.get_rva(offset)))
            else:
                self.offset_display.insert(index=tk.END, chars='%08x\n' % (offset))
            self.hex_display.insert(index=tk.END, chars=self.hex_strs[offset] + "\n")
            self.ascii_display.insert(index=tk.END, chars=self.ascii_strs[offset] + "\n")
            self.feature_display.insert(index=tk.END, chars=self.features[offset] + "\n")
            self.auto_annotation_display.insert(index=tk.END, chars=self.auto_annotations[offset] + "\n")
            self.user_comment_display.insert(index=tk.END, chars=self.user_comments[offset] + "\n")
        self.offset_display['state'] = 'disabled'
        self.hex_display['state'] = 'disabled'
        self.ascii_display['state'] = 'disabled'
        self.feature_display['state'] = 'disabled'
        self.auto_annotation_display['state'] = 'disabled'

    def launch_oid_browser(self):
        '''
        brings up a new gui frame allowing the user to set the oid.
        sets self.oid using the return value of the dialog.
        '''
        dialog = OidSelectDialog(self)
        self.oid = dialog.result
        if self.oid:
            self.clear_displays()
            self.create_display_strings(self.oid)
            self.display_file_data(self.oid)
            file_names = list(api.get_names_from_oid(self.oid))
            file_name = ', '.join(file_names)
            self.master.title(file_name)

    def create_comments(self, matches):
        comments ={}
        for oid in matches:
            comments[oid] = {}
            for function in matches[oid]['Functions']:
                for match in matches[oid]['Functions'][function]:
                    key = match.keys()[0]
                    start = match[key][0]
                    end = match[key][1]
                    comments[oid][start] = "Begin "+key[:-1]
                    comments[oid][end] = "End "+key[:-1]
        return comments

    def launch_template_browser(self):
        dialog = TemplateSelectDialog(self)
        template_name = dialog.result
        if template_name:
            self.clear_annotations_display()
            template_match = api.retrieve('alg_ident',self.oid,{'template':template_name})
            template_match = self.create_comments(template_match)
            for offset in self.offsets:
                if offset in template_match[self.oid]:
                    if self.auto_annotations[offset]:
                        self.auto_annotations[offset] += ', '
                    self.auto_annotations[offset] += template_match[self.oid][offset]
            self.display_annotation_data(self.oid)

    def clear_annotations_display(self):
        self.auto_annotation_display['state'] = 'normal'
        self.auto_annotation_display.delete(1.0, tk.END)
        self.auto_annotation_display['state'] = 'disabled'

    def display_annotation_data(self, oid):
        self.auto_annotation_display['state'] = 'normal'
        for offset in self.offsets:
            self.auto_annotation_display.insert(index=tk.END, chars=self.auto_annotations[offset] + "\n")
        self.auto_annotation_display['state'] = 'disabled'
        

class OidSelectDialog(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.transient(master)
        self.master = master
        self.result = None

        # create a frame to contain all window contents
        self.main_frame = ttk.Frame(self)

        # Have the columns all grow evenly when the window is resized.
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.columnconfigure(2, weight=0)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=0)

        #self.main_frame.grid(column=0, row=0, sticky='nsew')
        self.main_frame.pack(expand=True)

        # Listbox to contain the collection names
        self.collection_frame = ttk.Frame(master=self.main_frame)
        self.collection_frame['padding'] = 5
        self.collection_frame.grid(column=0, row=0, sticky='nsew')
        self.collection_scroll = ttk.Scrollbar(self.collection_frame)
        self.collection_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.collection_box = tk.Listbox(self.collection_frame)
        self.collection_box['width'] = 30
        self.collection_box['height'] = 10
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
        self.file_name_frame = ttk.Frame(master=self.main_frame)
        self.file_name_frame['padding'] = 5
        self.file_name_frame.grid(column=1, row=0, sticky='nsew')
        self.file_name_scroll = ttk.Scrollbar(self.file_name_frame)
        self.file_name_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_name_box = tk.Listbox(self.file_name_frame)
        self.file_name_box['width'] = 30
        self.file_name_box['height'] = 10
        self.file_name_box['font'] = 'TkFixedFont'
        self.file_name_box['borderwidth'] = 0
        self.file_name_box['highlightthickness'] = 0
        self.file_name_box.pack(fill=tk.BOTH, expand=1)
        self.file_name_box.bind('<<ListboxSelect>>', self.on_file_name_select)
        self.file_name_box.configure(yscrollcommand=self.file_name_scroll.set)
        self.file_name_scroll.configure(command=self.file_name_box.yview)

        # Display to contain the files attributes
        self.metadata_display = tk.Text(master=self.main_frame)
        self.metadata_display.grid(column=2, row=0, sticky='nsew')
        self.metadata_display['width'] = 30
        self.metadata_display['height'] = 10
        self.metadata_display['borderwidth'] = 4
        self.metadata_display['font'] = 'TkFixedFont'

        # buttons for cancel and ok
        self.button_box = ttk.Frame(self.main_frame)
        ok_button = ttk.Button(self.button_box, text="OK", width=10, 
                               command=self.ok, default=tk.ACTIVE)
        ok_button.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_button = ttk.Button(self.button_box, text="Cancel", width=10, 
                                   command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        self.button_box.grid(row=1, column=0, columnspan=3)

        # makes the dialog modal
        self.grab_set()

        # Make sure that an explicit close is treated as cancel
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (self.master.winfo_rootx()+50,
                                  self.master.winfo_rooty()+50))

        # moves the keyboard focus to the collection listbox
        self.collection_box.focus_set()

        # give every widget in the mainframe a little padding
        for child in self.winfo_children():
            child.grid_configure(padx=2, pady=2)

        # enters the local event loop and does not return
        # until this window is destroyed
        self.wait_window(self)

    def on_collection_select(self, event):
        try:
            index = int(self.collection_box.curselection()[0])
            self.current_collection = self.collection_box.get(index)
            self.file_name_box.delete(first=0, last=tk.END)
            collection_id = api.get_cid_from_name(self.current_collection)
            collection_features = api.retrieve('collections', collection_id)
            self.oids = collection_features['oid_list']
            for oid in self.oids:
                file_names = list(api.get_names_from_oid(oid))
                file_name = ', '.join(file_names)
                self.file_name_box.insert(tk.END, file_name)
        except IndexError:
            print "Index Error..."

    def on_file_name_select(self, event):
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

    def ok(self, event=None):
        try:
            index = int(self.file_name_box.curselection()[0])
            self.result = self.oids[index]
        except IndexError:
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, event=None):
        '''
        Puts focus back to the parent window,
        destroying this dialog.
        '''
        self.master.focus_set()
        self.destroy()


class TemplateSelectDialog(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.transient(master)
        self.master = master
        self.result = None

        # create a frame to contain all window contents
        self.main_frame = ttk.Frame(self)

        # Have the columns all grow evenly when the window is resized.
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=0)

        #self.main_frame.grid(column=0, row=0, sticky='nsew')
        self.main_frame.pack(expand=True)

        # Listbox to contain the collection names
        self.template_frame = ttk.Frame(master=self.main_frame)
        self.template_frame['padding'] = 5
        self.template_frame.grid(column=0, row=0, sticky='nsew')
        self.template_scroll = ttk.Scrollbar(self.template_frame)
        self.template_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_box = tk.Listbox(self.template_frame)
        self.template_box['width'] = 30
        self.template_box['height'] = 10
        self.template_box['font'] = 'TkFixedFont'
        self.template_box['borderwidth'] = 0
        self.template_box['highlightthickness'] = 0
        self.template_box.bind('<<ListboxSelect>>', self.on_template_select)
        self.template_box.pack(fill=tk.BOTH, expand=1)
        self.template_box.configure(yscrollcommand=self.template_scroll.set)
        self.template_scroll.configure(command=self.template_box.yview)
        self.template_names = os.listdir('core/libraries/templates')
        for template_name in self.template_names:
            self.template_box.insert(tk.END, template_name)


        # buttons for cancel and ok
        self.button_box = ttk.Frame(self.main_frame)
        ok_button = ttk.Button(self.button_box, text="OK", width=10, 
                               command=self.ok, default=tk.ACTIVE)
        ok_button.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_button = ttk.Button(self.button_box, text="Cancel", width=10, 
                                   command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        self.button_box.grid(row=1, column=0, columnspan=3)

        # makes the dialog modal
        self.grab_set()

        # Make sure that an explicit close is treated as cancel
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (self.master.winfo_rootx()+50,
                                  self.master.winfo_rooty()+50))

        # moves the keyboard focus to the collection listbox
        self.template_box.focus_set()

        # give every widget in the mainframe a little padding
        for child in self.winfo_children():
            child.grid_configure(padx=2, pady=2)

        # enters the local event loop and does not return
        # until this window is destroyed
        self.wait_window(self)

    def on_template_select(self, event):
        try:
            index = int(self.template_box.curselection()[0])
            fnames = self.template_box.get(index)
        except IndexError:
            print "Index Error..."

    def ok(self, event=None):
        try:
            index = int(self.template_box.curselection()[0])
            self.result = self.template_names[index]
        except IndexError:
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, event=None):
        '''
        Puts focus back to the parent window,
        destroying this dialog.
        '''
        self.master.focus_set()
        self.destroy()

def run_viewer_gui(args, opts):
    """ Plugin: starts the viewer GUI. Oxide processing is suspendended until
                the viewer GUI is dismissed.
        syntax: run_viewer_gui
    """
    app=FileView()
    app.mainloop()

def browser_wrapper():
    run_viewer_gui([],{})

def launch_viewer_gui(args, opts):
    """ Plugin: starts the viewer GUI as a separate thread, allowing oxide
                shell processing to continue
        syntax: launch_viewer_gui
    """
    t = threading.Thread(target=browser_wrapper)
    t.start()

exports = [run_viewer_gui, launch_viewer_gui]

if __name__ == '__main__':
    run_viewer_gui(None, None)
