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

import os, logging, time, cPickle, types, traceback, sys, shutil, sys_utils
from collections import defaultdict
from glob import glob 
import oxide as local_oxide
import shell_api
from otypes import cast_string
from cmd import Cmd
from code import InteractiveConsole, InteractiveInterpreter

dict_type = (dict, defaultdict)
collection_type = (list, set, tuple)
modifiers = ("%", "&", "$", "@", "-", "^")
readline_enabled = False
readline_fullversion = False #readline on windows doens't have the remove_history_item func
try:
    import readline
    import rlcompleter
    # Allows for tab complete of directories
    # readline uses either the libedit (Mac) or GNU libraries (Everyone Else), differentiated in the docstring
    if readline.__doc__ and 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    readline.set_completer_delims(readline.get_completer_delims().replace(os.path.sep, ""))
    readline_enabled = True
    readline.remove_history_item
    readline_fullversion = True
except ImportError: 
    logging.error("Failed to import readline.  Tab complete and command history will not work.")
except AttributeError:
    logging.debug("Readline does not have remove_history_item function.")



def error_handler(f):
    def wrapper(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except (ShellSyntaxError, ShellRuntimeError) as se:
            print se.err
            if f.__name__ != "default":
                print f.__doc__
        except Exception as se:
            print '-'*60
            traceback.print_exc()
            print '-'*60
    wrapper.__name__ = f.__name__
    wrapper.__doc__  = f.__doc__
    return wrapper

class ShellSyntaxError(Exception):
    def __init__(self, err):
        self.err = "  ShellSyntaxError: " + err

class ShellRuntimeError(Exception):
    def __init__(self, err):
        self.err = "  ShellRuntimeError: " + err

class EmbeddedConsoleExit(SystemExit):
    pass
    
class Statekeeper(object):
    def __init__(self, obj, attribs):
        self.obj = obj
        self.attribs = attribs
        if self.obj:
            self.save()
    def save(self):
        for attrib in self.attribs:
            setattr(self, attrib, getattr(self.obj, attrib))
    def restore(self):
        if self.obj:
            for attrib in self.attribs:
                setattr(self.obj, attrib, getattr(self, attrib)) 


# A "global" list of plugins needed by the plugin manager GUI.
plugin_list = []
# A reference to the oshell instance. Similar to a singleton. This is UGLY python - Rig.
instance = None

class OxideShell(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        global instance
        try:
            if self.oxide:
                pass
        except AttributeError:
            self.oxide = local_oxide
            
        self.name = "oshell"
        self.logger = logging.getLogger(self.name)
        self.logger.debug("init")
        
        self.logger.debug("Initializing local config")
        self.config = { "promptcolor"     : "cyan",
                        #"prompt"          : self.colorize("\n oxide > ", "cyan"),
                        "prompt"          : " oxide > ",
                        "max_processes"   : local_oxide.config.multiproc_max,
                        "multiprocessing" : local_oxide.config.multiproc_on,
                        "header_len"      : 40,
                        "context_limit"   : 250,
                        "file_max"        : local_oxide.config.file_max,
                        "verbosity"       : logging.getLevelName(local_oxide.config.verbosity_level),
                        "context_file"    : ".context.save",
                      }
                      
        self.prompt  = self.config["prompt"]
        self.intro   = "\n --------   Oxide   -------- \n"
        self.context = [] # [ (oid, set(names) ) ]

        self.plugins     = {}
        self.plugin_vars = {}
        self.pystate     = {}
        self.vars        = defaultdict(dict)
        self.stop        = None # Used to signal the exit of the shell
        self.aliases     = self.alias()
        self.use_rawinput = True

        self.logger.debug("Initializing commands")
        self.commands = {}
        for i in dir(self):
            if i.startswith("do_") and i.lower() not in ("do_eof", "q"):
                self.commands[i.replace("do_", "")] = ()
        
        self.logger.debug("Initializing subcommands")
        self.commands["tag"] = ("apply", "get", "filter")
        self.commands["show"] = ("collections", "context", "modules", "stats", 
                                 "orphans", "vars", "plugins", "aliases")
        self.show_completions = ("collections", "context", "modules ", "stats", 
                                 "orphans", "vars", "plugins ", "aliases")
        self.commands["context"] = ("add", "clear", "remove", "set", "load", "save")
        self.commands["collection"] = ("create", "delete", "rename", "add", "remove")
        self.commands["history"] = ("clear")
        self.commands["drop"] = ("database", "scratch", "localstore", "orphans")
        
        self.logger.debug("Loading plugins noted in config")
        for p in local_oxide.config.plugins:
            self.do_plugin(p)

        self.logger.debug("Loading history file")
        if readline_enabled:
            try:
                if not os.path.isfile(local_oxide.config.history_file):
                    readline.write_history_file(local_oxide.config.history_file)
                readline.read_history_file(local_oxide.config.history_file)
                readline.set_history_length(local_oxide.config.history_max)
            except IOError:
                #print " - History file %s seems to be corupted. Trying to remove." % (local_oxide.config.history_file)
                #os.remove(local_oxide.config.history_file)
                pass
        instance = self
        shell_api.parse_argument = self.parse_argument 

        
    ### PRE/POST FUNCTIONS #####################################################
    def preloop(self):
        pass
    
    def postloop(self):
        pass
    
    def precmd(self, line):
        return line
        
    def postcmd(self, stop, line):
        if self.config["multiprocessing"] != self.oxide.config.multiproc_on:
            self.oxide.config.multiproc_on = self.config["multiprocessing"]
        
        if self.config["max_processes"] != self.oxide.config.multiproc_max:
           self.oxide.config.multiproc_max = self.config["max_processes"]
        
        if isinstance(self.config["verbosity"], str):
            self.config["verbosity"] = self.config["verbosity"].upper()
            if type(logging.getLevelName(self.config["verbosity"])) == int:
                if local_oxide.config.verbosity_level != self.config["verbosity"]:
                    self.oxide.set_verbosity_level(self.config["verbosity"])
                    
        if self.config["file_max"] != self.oxide.config.file_max:
            local_oxide.config.file_max = self.config["file_max"]
        
        # colorize messes up readline self.config["prompt"] = self.colorize(self.config["prompt"], self.config["promptcolor"])
        self.prompt = self.config["prompt"]
        
        line = "" # Reset the line
        return self.stop

    def emptyline(self):
        pass
        
    ### DO COMMANDS ############################################################
    @error_handler
    def do_py(self, line): 
        """
    Description: A Python interative shell with shared state of the Oxide shell
    Syntax: py [<python_command>] 
        """
        
        self.pystate['self'] = self

        # Put the oxide vars in the py env
        for v in self.vars:
            self.pystate[v] = self.vars[v]

        interp = InteractiveConsole(locals=self.pystate)
        interp.runcode('import sys, os;sys.path.insert(0, os.getcwd())')
        
        if line:
            interp.runcode(line)
            for v in self.pystate:
                if v not in ('__builtins__', 'self', 'sys', 'os'):
                    self.vars[v] =  self.pystate[v]
        else:
            def run(line):
                try:
                    file = open(line)
                    interp.runcode(file.read())
                    file.close()
                except IOError, e:
                    self.perror(e)
            
            def quit():
                raise EmbeddedConsoleExit
            
            self.pystate['quit'] = quit
            self.pystate['exit'] = quit
            try:
                cprt = 'Type "help", "copyright", "credits" or "license" for more information.'        
                keepstate = Statekeeper(sys, ('stdin','stdout'))
                sys.stdout = self.stdout
                sys.stdin = self.stdin
                interp.interact(banner= "Python %s on %s\n%s\n(Python Interactive Shell which shares state with Oxide)\n" %
                       (sys.version, sys.platform, cprt))
                       
            except EmbeddedConsoleExit:
                pass
                
            for v in self.pystate: # Put our py local vars back into the oxide env
                if v not in ('quit', 'run', '__builtins__', 'self', 'cmd', 'sys', 'exit', 'os'):
                    self.vars[v] = self.pystate[v]
            
            keepstate.restore()


    @error_handler
    def do_history(self, line):
        """
    Description: Show the command history
    Syntax: history [clear]
        """
        if not readline_enabled:
            print " - This command is disabled because it depends on readline"
            return
        
        if readline_fullversion and readline.get_current_history_length() != 0:
            readline.remove_history_item(readline.get_current_history_length()-1)
        if line.strip() == "clear":
            print "  - Clearing history"
            readline.clear_history()
            return
        
        self.print_header("Oxide Shell History")
        if readline.get_current_history_length() < 1:
            print "      <EMPTY>"
            return
            
        for i in xrange(readline.get_current_history_length()+1):
            item = readline.get_history_item(i)
            if item:
                self.print_item(item)

    @error_handler
    def do_drop(self, line):
        """
    Description: Intelligently deletes Oxide data and OIDs

    Syntax:
        drop database
        drop scratch
        drop localstore
        drop orphans
        drop &<collection>
        drop $<context>
        show %<oid>
        """
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("drop "+line)
        self.parse_pipe(commands)


    @error_handler
    def do_load(self, line):
        """
    Description: Load a file and execute the commands in it
    Syntax: load <file>
        """
        if not line:
            raise ShellSyntaxError("")
            
        if not os.path.isfile(line):
            raise ShellRuntimeError("File %s not found" % line)
        
        fd = file(line, "r")
        lines = fd.readlines()
        fd.close()
        for line in lines:
            line = line.strip()
            if line:
                commands = self.parse_line(line)
                self.parse_pipe(commands)
            

    @error_handler
    def do_bash(self, line):
        """
    Description: Execute a command as if at the OS prompt
    Syntax: bash <command>
        """
        if not line:
            raise ShellSyntaxError("")
        os.system(line)
        
 
    @error_handler
    def do_configure(self, line):
        """
    Description: Set or display shell 
    Syntax: configure [ --<item>=<value> ]
        """
        if not line:
            self.print_item(self.config, header="Oxide Shell Config")
            return
            
        commands = self.parse_line("configure "+line)
        self.parse_pipe(commands)
        
    
    @error_handler
    def do_exit(self, line):
        """
    Description: Exit the shell
    Syntax: exit
        """
        if readline_enabled:
            remove = []
            if readline_fullversion:
                for i in xrange(readline.get_current_history_length(), 0, -1):
                    if readline.get_history_item(i) in ("q", "exit"): 
                        remove.append(i)
                for i in remove:
                    readline.remove_history_item(i-1)
            readline.write_history_file(local_oxide.config.history_file)
        self.stop = True
    do_EOF = do_exit

    @error_handler
    def do_clear(self, line):
        """
    Description: Clear the console
    Syntax: clear
        """
        os.system(['clear','cls'][os.name == 'nt'])
    
    @error_handler
    def default(self, line):
        """
    Description: This will be called if the command does not match any other
        """   
        for a in self.aliases:
            if line.startswith(a):
                f = self.aliases[a]
                return f(line.strip(a))
        
        commands = self.parse_line(line)
        self.parse_pipe(commands)
    
    @error_handler
    def do_show(self, line):
        """
    Description: Print info about an item
    Syntax:
        show &<collection> [--verbose]
        show $<context>
        show @<var>
        show %<oid>
        
        show modules [<module>] [--verbose]
        show collections [--verbose]
        show context
        show stats
        show orphans
        show vars
        show plugins
        show aliases
        """
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("show "+line)
        self.parse_pipe(commands)
    
    
    @error_handler
    def do_context(self, line):
        """
    Description: Manipulate the context which is like a working set
    Syntax:        
        context set %<oid> # Set context to this (e.g. clear, then add)
        
        context add %<oid> # Append to the current context
        
        context remove %<oid> # Remove this from context
    
        context clear # Empty out the context
        
        context save [<fname>] # Save a context to a file
        
        context load [<fname>] # Load a context from a file

        """
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("context "+line)
        self.parse_pipe(commands)



    @error_handler
    def do_tag(self, line):
        """
    Syntax:
        tag get %<oid> 
        tag apply <tag>:<value> %<oid>  
        tag filter <tag>:<value> [ $<context> ... opts ]
        
        opts example:
          --year=2011  --month=12  --day=31
        """ 
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("tag "+line)
        self.parse_pipe(commands)
                
                
    @error_handler
    def do_run(self, line):
        """
    Description: Execute a module
    Syntax: run <module> %<oid> [ --<opt>=<val> ]
        """ 
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("run "+line)
        self.parse_pipe(commands)
            

    @error_handler
    def do_import(self, line):
        """
    Description: Import file(s) or directories
    Syntax: import <file1> | <directory1> | *.exe
        """ 
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("import "+line)
        self.parse_pipe(commands)
            
            
    @error_handler
    def do_plugin(self, line):
        """
    Description: Load a plugin file
    Syntax: plugin <plugin_file>
    Note: the file needs the .py extention but .py is dropped when executing the command
        """
        if not line:
            raise ShellSyntaxError("")
        line = line.split()
        for p in line:
            try:
                plugin_obj = __import__("plugins." + p)
                if p in self.plugins:
                    import sys
                    del sys.modules["plugins."+p]
                    del self.plugins[p]
                    del plugin_obj
                    if p in plugin_list:
                        plugin_list.remove(p)
                    plugin_obj = __import__("plugins." + p)
                self.plugins[p] = getattr(plugin_obj, p).exports
                plugin_list.append(p)
                try:
                    cmds = getattr(plugin_obj, p).commands
                    for f in cmds:
                        self.commands[f.__name__] = cmds[f]
                except:
                    cmds = {}
                getattr(plugin_obj, p).ShellSyntaxError = ShellSyntaxError
                getattr(plugin_obj, p).ShellRuntimeError = ShellRuntimeError
                getattr(plugin_obj, p).api = self.oxide
                getattr(plugin_obj, p).shell_api = shell_api
                if p+"_init" in dir(getattr(plugin_obj, p)): # If the plugin has an _init() call it
                   getattr(getattr(plugin_obj, p), p+"_init")([],{})
                if "variables" in dir(getattr(plugin_obj, p)):
                    self.plugin_vars[p] = getattr(plugin_obj, p).variables

            except (ShellRuntimeError, ImportError) as e:
                try:
                    plugin_obj = __import__("plugins_dev." + p)
                    if p in self.plugins:
                        import sys
                        del sys.modules["plugins_dev."+p]
                        del self.plugins[p]
                        del plugin_obj
                        plugin_obj = __import__("plugins_dev." + p)
                    self.plugins[p] = getattr(plugin_obj, p).exports

                    try:
                        cmds = getattr(plugin_obj, p).commands
                        for f in cmds:
                            self.commands[f.__name__] = cmds[f]
                    except:
                        cmds = {}

                    getattr(plugin_obj, p).ShellSyntaxError = ShellSyntaxError
                    getattr(plugin_obj, p).ShellRuntimeError = ShellRuntimeError
                    getattr(plugin_obj, p).api = self.oxide
                    getattr(plugin_obj, p).shell_api = shell_api
                    if p+"_init" in dir(getattr(plugin_obj, p)): # If the plugin has an _init() call it
                       getattr(getattr(plugin_obj, p), p+"_init")([],{})
                    if "variables" in dir(getattr(plugin_obj, p)):
                        self.plugin_vars[p] = getattr(plugin_obj, p).variables

                except (ShellRuntimeError, ImportError) as e:
                    if type(e) is ImportError and e.__str__() != 'No module named ' + p:
                        import traceback
                        print traceback.print_exc()
                    else:
                        print "  - Unable to load plugin %s." %p
            except AttributeError as e:
                if e.__str__() == "'module' object has no attribute 'exports'":
                    print "  - Missing exports in plugin %s. Plugin load aborted." %p
                else:
                    import traceback
                    print traceback.print_exc()


    @error_handler
    def do_collection(self, line):
        """
    Description: Manipulate a collection which are persistent sets of items
    Syntax:
        collection create <collection> %<oid> 
        collection delete <collection>
        collection rename <collection> <new_name>
        collection remove <collection> %<oid>
        """
        if not line:
            raise ShellSyntaxError("")
        commands = self.parse_line("collection "+line)
        self.parse_pipe(commands)
    
    def do_example(self, line):
        """
    - Commands can be piped into each other. This command imports 
      files and creates a collection from the files imported.
    
    import datasets/sample_dataset | collection create sample
    
    - The show command is used to print to the screen
    
    show &<collection>
    
    - The 'pipe' command can be used to send the content of an
      item into a plugin function
      
    &<collection> | random_sample | count
    
        
    - Assign the output of a pipe to a variable
    
    &<collection> | @x 
    
    
    - Pipe the output of a variable
    
    @x | show
        """
        print self.do_example.__doc__
    
    def do_help(self, line):
        """  - System modifiers that resolve to an oid:
        %<oid>
        &<collection>
        $<context>
        @<var>
        ^<file_name>
        
        
  - help <command> for command specific help
        
  - See example for further information
        
        """
        if line:
            if line in self.commands:
                f = getattr(self, "do_"+line)
            elif line in self.plugin_function_names():
                f = self.get_plugin_function(line)
            elif line in self.plugins:
                try:
                    module = sys.modules["plugins."+line]
                except KeyError:
                    module = sys.modules["plugins_dev."+line]
                print "\n\n"
                print module.__doc__, "\n"
                for func in self.plugins[line]:
                    print "   ", func.__name__, ":",
                    print func.__doc__
                return
            else:
                print " - Command %s not found" % (line)
                return
                                  
            print f.__doc__
            
        else:
            self.print_header("Oxide Shell Help")
            commands = self.commands.keys()
            commands.sort()
            print "  - Commands: " + ", ".join(commands)
            print
            print self.do_help.__doc__
            
            
    ### FUNCTIONALITY FOR DO COMMANDS ##########################################
    def configure(self, args, opts):
        if args or not opts:
            raise ShellSyntaxError("Invalid syntax")
            
        for opt in opts:
            if not opt in self.config:
                raise ShellSyntaxError("%s is not a config key" % opt)
            self.config[opt] = opts[opt]
    
    def tag(self, args, opts):
        if len(args) < 2:
            raise ShellSyntaxError("")

        subcommand, items = args[0], args[1:]
        if subcommand not in self.commands["tag"]:
            raise ShellSyntaxError("Command %s invalid" % subcommand)
            
        if subcommand == "get": # tag get oid ...
            items = self.oxide.flatten_list(items)
            for item in items:
                tags = self.oxide.get_tags(item)
                self.print_item(tags, header="Tags:"+item)
                self.print_header()
            return items
        
        elif subcommand == "filter": # tag filter <tag>:<value> [ oid ... ]
            tags = items[0]
            items = items[1:]
            tag, value = self.tag_value_split(tags)
            if len(items) == 0: items == None
            valid, invalid = self.oxide.valid_oids(items)
            oid_list = self.oxide.tag_filter(valid, tag, value)
            oid_list = self.time_filter(oid_list, opts)
            self.print_item(oid_list, header="Tag Filter Results")
            return oid_list
        
        if len(items) < 2:
            raise ShellSyntaxError("")
         
        tags = items[0]
        items = items[1:]
        
        if subcommand == "apply": # tag apply <tag>:value> oid ...
            tag, value = self.tag_value_split(tags)
            self.oxide.apply_tags(items, {tag:value})
            print "  - Applied tag %s:%s to %s item(s)" % (tag, value, len(items)) 
            return items 
            

    def collection(self, args, opts):
        if len(args) < 2:
            raise ShellSyntaxError("")
            
        subcommand, collection_name = args[0], args[1]
        valid, invalid = self.oxide.valid_oids(args[2:])
        valid = self.oxide.expand_oids(valid)
        if subcommand not in self.commands["collection"]:
            raise ShellSyntaxError("Command %s invalid" % subcommand)
        
        notes = ""
        if "notes" in opts: notes = opts["notes"]
        
        if subcommand == "create": # collection create <collection> oid ...
            if self.oxide.exists("files", collection_name):
                raise ShellSyntaxError("Attempted to create a collection with oid %s as the name" % collection_name)
            if not self.oxide.create_collection(collection_name, valid, notes):
                print "  - Not able to create collection %s" % (collection_name)
                return []
            print "  - Collection %s created" % (collection_name)
            cid = self.oxide.get_cid_from_oid_list(valid)
                
        if not collection_name in self.oxide.collection_names():
            raise ShellSyntaxError("Collection %s does not exist" % collection_name)
            
        if subcommand == "delete": # collection delete <collection>
            if self.oxide.delete_collection_by_name(collection_name):
                print "  - Collection %s deleted" % (collection_name)
            else:
                print "  - Not able to delete collection %s" % (collection_name)
                
        elif subcommand == "rename": # collection rename <collection> <new_name>
            if len(invalid) < 1:
                raise ShellSyntaxError("New name not provided")
            new_name = invalid[0]
            if not self.oxide.rename_collection_by_name(collection_name, new_name):
                return []
            print "  - Collection renamed from %s to %s" % (collection_name, new_name)
            collection_name = new_name
            invalid.remove(new_name)
            
        elif subcommand == "remove": # collection remove <collection> oid ...
            if not self.oxide.prune_collection_by_name(collection_name, valid):
                return []
            print "  - %s item(s) removed from collection %s" % (len(valid), collection_name)
        
        if invalid:
            print "  - Invalid oids not processed: "
            self.print_item(invalid)
        
        cid = self.oxide.get_cid_from_name(collection_name)
        if not cid or not self.oxide.exists("collections", cid):
            return []
        return [cid]
            
            
    def show(self, args, opts):
        if not args:
            print "  - Nothing to show"
            return args
            
        if args[0] in self.commands["show"]:
            subcommand = args[0]
            args = args[1:]
            if subcommand == "collections": # show collections
                self.print_collections(args, opts)
                
            elif subcommand == "context": # show context
                verbose = False
                if "verbose" in opts:
                    verbose = True
                self.print_context(verbose)
                args = [ entry[0] for entry in self.context ]
                
            elif subcommand == "modules": # show modules
                self.print_modules(args, opts)
                
            elif subcommand == "stats": # show stats
                mod_stats = self.oxide.modules_stats()
                self.print_item(mod_stats, "Modules Stats")
                
            elif subcommand == "vars": # show vars
                self.print_item(self.vars, "Variables")
                if not self.vars:
                    print "  <EMPTY>"
                print
                self.print_item(self.plugin_vars, "Plugin Variables")
                if not self.plugin_vars:
                    print "  <EMPTY>"
                    
            elif subcommand == "plugins": # show plugins
                self.print_header("Plugins")
                if self.plugins:
                    self.print_item(self.plugins)
                else:
                    print "  <EMPTY>"
                self.print_header()
                    
            elif subcommand == "aliases": # show aliases
                aliases = {}
                for a in self.aliases:
                    aliases[a] = self.aliases[a].__name__.strip("do_")
                self.print_item(aliases, "Aliases")
            
            elif subcommand == "orphans": # show orphans
                oids = self.oxide.retrieve_all_keys("file_meta")
                if not oids:
                    print "  <EMPTY>"
                    return
                oids = set(oids)
                for cid in self.oxide.collection_cids():
                    ids = self.oxide.get_field('collections', cid, 'oid_list')
                    if ids:
                        ids = set(ids)
                        oids = oids - ids
                self.print_header("Orphan oids")
                if oids:
                    self.print_item(oids, bullet="  - ")
                else:
                    print "  <EMPTY>"
                self.print_header()
                args = oids
                
        else: # show item
            if isinstance(args, collection_type) or isinstance(args, dict_type):
                for item in args:
                    self.print_info(item, opts)
            else:  
                print args
        return args


    def drop(self, args, opts):
        if not args:
            print "  - Nothing to drop"
            return args

        logger = logging.getLogger("oxide")
        count = 0
        
        if args[0] in self.commands["drop"]:
            subcommand = args[0]
            path = ""

            if sys_utils.query("Are you sure you want to delete '%s'?" % subcommand,"no"):
                if subcommand == "database": # drop database
                    path = os.path.dirname(self.oxide.scratch_dir) + "/db"
                elif subcommand == "scratch": # drop scratch
                    path = self.oxide.scratch_dir
                elif subcommand == "localstore": # drop localstore
                    path = os.path.dirname(self.oxide.scratch_dir) + "/localstore"

                if path != "":
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            os.unlink(os.path.join(root, f))
                        for d in dirs:
                            shutil.rmtree(os.path.join(root, d))

                    print "  - Deleted contents of %s" % path
                elif subcommand == "orphans": # drop orphans
                    oids = self.oxide.retrieve_all_keys("file_meta")
                    if oids:
                        oids = set(oids)
                        for cid in self.oxide.collection_cids():
                            ids = self.oxide.get_field('collections', cid, 'oid_list')
                            if ids:
                                ids = set(ids)
                                oids = oids - ids
                    logger.setLevel(logging.CRITICAL)

                    for oid in oids:
                        self.oxide.flush_oid(oid)
                        count += 1

                    logger.setLevel(logging.WARNING)

                    print "  - Dropped %d orphan OID(s)" % count
        else: # drop <oid> | <collection>
            if sys_utils.query("Are you sure you want to delete collection or OID?","no"):
                valid, invalid = self.oxide.valid_oids(args)
                valid_oids = self.oxide.expand_oids(valid)

                logger.setLevel(logging.CRITICAL)

                for oid in valid_oids:
                    self.oxide.flush_oid(oid)
                    count += 1

                logger.setLevel(logging.WARNING)

                self.context = []
                print "  - Dropped %d OID(s)" % count
                print "  - Context cleared"

        # Remove Empty Directories
        for root, dirs, files in os.walk(os.path.dirname(self.oxide.scratch_dir) + "/db"):
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                except:
                    pass

        return args

    
    def context_command(self, args, opts):
        if not args:
            raise ShellSyntaxError("Subcommand required for context")
        subcommand = args[0]
        args = args[1:]
        if subcommand not in self.commands["context"]:
            raise ShellSyntaxError("Command %s invalid" % subcommand)
        
        elif subcommand == "add": # context add oid ...
            new_context = self.build_context([subcommand, args])
            if not new_context:
                raise ShellRuntimeError("Nothing found to add to context")
            self.context.extend(new_context)
            print "  - %s item(s) added to the context" % (len(new_context))
        
        elif subcommand == "clear": # context clear
            self.context = []
            print "  - Context cleared"
        
        elif subcommand == "remove": # context remove oid ...
            rm_context = self.build_context([subcommand, args])
            if not rm_context:
                raise ShellRuntimeError("Nothing to remove from the context")
            self.context = [ i for i in self.context if i not in rm_context ] 
            print "  - %s item(s) removed from the context" % (len(rm_context))
        
        elif subcommand == "load": # context load <fname>
            self.load_context(args)
                
        elif subcommand == "save": # context save <fname>
            self.save_context(args)
            
        elif subcommand == "set": # context set oid ...
            new_context = self.build_context([subcommand, args])
            if not new_context:
                raise ShellRuntimeError("Nothing found to set the context to")
            self.context = new_context
            print "  - Context cleared and set to %s items" % (len(new_context))
            
        return [ entry[0] for entry in self.context ]

    
    def run_module(self, args, opts): # run <module> oid ...
        show = False
        mod_list = self.oxide.modules_list()
        module_name = args[0]
        args = args[1:]
        value = None
        this_opts = opts
        if "opts" in opts:
            o = opts["opts"]
            if isinstance(o, str) and o in self.vars:
                o = self.vars[o]
            if isinstance(o, dict):
                this_opts = o
            else:
                raise ShellSyntaxError("Invalid options specified %s" % o)
            
        if module_name not in mod_list:
            raise ShellSyntaxError("Unrecognized Module %s" % module_name)
        valid, invalid = self.oxide.valid_oids(args)
        print "  - Running %s over %d items" %(module_name, len(valid))
        if "pipe" in opts:
            value = self.oxide.retrieve(module_name, valid, this_opts)
            if "show" in opts:
                self.print_header(text="Results")
                self.print_item(value)
                self.print_header()
            if "var" in opts:
                self.vars[opts["var"]] = value
                print "  - Variable %s assigned."%opts["var"]
        else:
            self.oxide.process(module_name, valid, this_opts)

        if invalid:
            print "  - Invalid oid's not processed: "
            self.print_item(invalid)
               
        return value


    def import_files(self, args, opts, verbose=True): # import <file> | <dir> ...
        oid_list = []
        total_new = 0
        for arg in args:
            if os.path.isfile(arg): # Import a file
                oid, new_file = self.oxide.import_file(arg)
                if not oid:
                    print "  - Not able to import file %s" % (arg) 
                    continue
                oid_list.append(oid)
                total_new += new_file
            elif os.path.isdir(arg): # Import a directory
                oids, new_files = self.oxide.import_directory(arg)
                if not oids:
                    print "  - Not able to import diretory %s" % (arg) 
                    continue
                oid_list.extend(oids)
                total_new += new_files
            elif "*" in arg: # Import glob
                oids = self.import_files(glob(arg), opts, verbose=False)
                if not oids:
                    print "  - Not able to import glob %s" % (arg) 
                    continue
                oid_list.extend(oids)
            else:
                print "  - %s is not a file or directory, skipping" % (arg)
        
        if not oid_list and verbose:
            print "  - No files were imported"
        elif verbose:
            print "  - %s file(s) imported, %s are new" % (len(oid_list), total_new)
        
        return oid_list
                 

    ### PARSE LINE #############################################################
    def parse_line(self, line):
        """ Given a string with commands, args and opts build a commands tuple
        """
        commands = []
        for command in line.split('|'):
            opts = {}
            args = []
            words = command.split()
            if not words:
                raise ShellSyntaxError("Empty command")
            args.append(words[0])
            for p in words[1:]:
                arg, opt = self.parse_argument(p)
                if opt:
                    opts[opt[0]] = opt[1]
                elif isinstance(arg, list):
                    args.extend(arg)
                elif arg:
                    args.append(arg)
            commands.append((args, opts))
        return commands
        
        
    def parse_pipe(self, commands):
        """ Peel off a command and pass the results to the next command in the pipe
        """
        if not commands:
            return

        cur_command, commands = commands[0], commands[1:]
        args, opts = cur_command[0], cur_command[1]
        command, args = args[0], args[1:]
        
        if command in self.aliases:
            command = self.aliases[command]
        
        res = []
        if command == "collection": # ... | collection ... | ...
            res = self.collection(args, opts)
        elif command == "import": # ... | import ... | ...
            res = self.import_files(args, opts)       
        elif command == "run": # ... | run ... | ...
            if commands:
                opts["pipe"] = True
            res = self.run_module(args, opts)
        elif command == "tag": # ... | tag ... | ...
            res = self.tag(args, opts)
        elif command == "context": # ... | context ... | ...
            res = self.context_command(args, opts)
        elif command == "show": # ... | show ... | ...
            res = self.show(args, opts)
        elif command == "drop": # ... | drop ... | ...
            res = self.drop(args, opts)
        elif command == "configure":
            res = self.configure(args, opts)
        elif command[0] in ("%", "$", "&", "^"): # %<oid> $<context> &<collection> or ^<name>
            res, opt = self.parse_argument(command)
            if not isinstance(res, list):
                res = [res]
            res.extend(args)
            args = []
        elif command[0] == "@": # @<var> or ... | @<var>
            var = command[1:]
            if not var:
                raise ShellSyntaxError("Empty variable")
            if not args:
                if var in self.vars:
                    res = self.vars[var]
                    if not isinstance(res, list):
                        res = [res]
                    res.extend(args)
                    args = []
                else:
                    raise ShellSyntaxError("Variable %s used without being defined."%var)
            else:
                self.vars[var] = args
                res = self.vars[var]
        else: # Look for plugins functions
            func = None
            for p in self.plugins:
                for f in self.plugins[p]:
                    if command == f.__name__:
                        func = f
            if func:
                res = func(args, opts)
            else:
                raise ShellSyntaxError("Command %s not found."%command)
        if commands:
            if isinstance(res, list):
                commands[0][0].extend(res)
            else:
                commands[0][0].append(res)
        self.parse_pipe(commands)
        
        
    def parse_argument(self, a):
        """ Given a string with the modifiers below resolve to an oid
            or return the object pass in unchanged
        """
        t = a[0] 
        if t not in modifiers:
            return a, None
            
        elif len(a) < 2:
            raise ShellSyntaxError("Argument %s is incomplete" % a)
        
        m = a[1:]
        if t == "@": # Variable
            var = m
            if not var:
                raise ShellSyntaxError("Empty variable")
            if not var in self.vars:
                raise ShellSyntaxError("Variable %s does not exist" % var)
            return self.vars[var], None
                
        elif t == "%": # oid
            oid = m
            if not self.oxide.source(oid):
                raise ShellSyntaxError("oid %s does not exist" % oid)
            return oid, None
        
        elif t == "$": # Context
            try:
                l = self.resolve_context(m)
            except TypeError:
                raise ShellSyntaxError("Context index %s error" % m) 
            if isinstance(l, tuple):
                return l[0], None
            else:
                return [ i[0] for i in l ], None
                
        elif t == "&": # Collection
            col_name = m
            if col_name not in self.oxide.collection_names():
                raise ShellSyntaxError("Collection %s does not exist" % col_name)
            return self.oxide.get_cid_from_name(col_name), None

        elif t == "^": # Name
            name = m
            oid_dict = self.oxide.get_oids_with_name(name) # This will be slow on large systems - need a reverse lookup index
            return oid_dict.keys(), None # Just return a list of the oids

        elif t == "-": # Option
            if m and m[0] == "-":
                opt = m[1:]
                opts = opt.split("=")
                if len(opts) == 1:
                    return None, (opts[0], "")
                elif len(opts) == 2:
                    if opts[1][0] == "@":
                        var = opts[1][1:]
                        if var not in self.vars:
                            raise ShellSyntaxError("Invalid variable %s" % var)
                        else:
                            return None, (opts[0], self.vars[var])
                    else:
                        return None, (opts[0], cast_string(opts[1]))
                else:
                    raise ShellSyntaxError("Invalid option %s" % a)
            else:
                return a, None
            
        
    ### CONTEXT MANIPULATIONS ##################################################
    def save_context(self, line):
        """ Save the current context to a file
        """
        if not self.context:
            print "  - Context is empty"
            return
            
        if not line:
            fname = self.config["context_file"]
        else:
            fname = line[0]
        
        if os.path.isdir(fname):
            print "  - A directory named %s already exists. Aborting context save." % (fname)
            return
        if os.path.isfile(fname):
            res = raw_input("  - File %s already exists. Overwrite it (y/N)? ").strip().lower() % (fname)
            if res != 'y':
                print "  - Aborting context save"
                return
                
        fd = open(fname, 'wb')
        cPickle.dump(self.context, fd)
        fd.close()
        print "  - Context saved to file %s" % (fname)
        
        
    def load_context(self, line):
        """ Set the current connect to a context that has been saved to a file 
        """
        if not line:
            fname = self.config["context_file"]
        else:
            fname = line[0]
        
        if not os.path.isfile(fname):
            print "  - Context file %s does not exist" % (fname)
            return
            
        fd = open(fname, 'rb')
        file_context = cPickle.load(fd)
        if not self.valid_context(file_context):
            print "  - Aborting context load"
            return
            
        self.context = file_context 
        fd.close()
        print "  - Context loaded from file %s" % (fname)
       
                 
    def valid_context(self, context):
        """ Context format [ (oid, set(names) ) ]
        """
        try:
            if not isinstance(context, list):
                 raise ShellRuntimeError("Context corrupted")
            for i in context:
                if not isinstance(i, tuple):
                    raise ShellRuntimeError("Context corrupted")
                elif len(i) != 2:
                    raise ShellRuntimeError("Context corrupted")
                elif not isinstance(i[0], str):
                    raise ShellRuntimeError("Context corrupted")
                elif not self.oxide.source(i[0]) or self.oxide.source(i[0]) == "collections":
                    raise ShellRuntimeError("oid:%s in context does not exist" % i[0])
                elif not isinstance(i[1], set):
                    raise ShellRuntimeError("Context corrupted")
                for n in i[1]:
                    if not isinstance(n, str):
                        raise ShellRuntimeError("Context corrupted")
                        
        except ShellRuntimeError as e:
            print e.err
            return False
            
        return True
        
        
    def resolve_context(self, arg):
        if arg.startswith("$"):
            arg = arg[1:] 
        if arg.count(":") == 1:
            for i in arg.split(":"):
                if i!="" and (not i.isdigit() or int(i)>len(self.context)-1):
                    raise ShellRuntimeError("Context index %s out of range" % i)
        elif not arg.isdigit() or int(arg)>len(self.context)-1:
            raise ShellRuntimeError("Context index %s out of range" % arg)
        return eval("self.context["+arg+"]")
    
    
    def build_context(self, items):
        """ Build a list of items suitable for the context
        """
        valid, invalid = self.oxide.valid_oids(items)
        new_context = []
        oid_list = self.oxide.expand_oids(valid)
        nitems = len(oid_list)
        if nitems > self.config["context_limit"]:
            res = raw_input(" Are you sure you want to fill the context with " + str(nitems) + " items? (y/N) ").strip().lower()
            if res != 'y':
                return new_context
        
        for oid in oid_list:
            src_type = self.oxide.source(oid)
            if src_type == "files":
                fnames = self.oxide.get_field("file_meta", oid, "names")
            elif src_type == "vmem_procs":
                fnames = self.oxide.get_field("vmem_procs_meta", oid, "names")
            else:
                fnames = [oid]
            entry = (oid, fnames)
            new_context.append(entry)
        return new_context


    ### PRINT ##################################################################
    def print_item(self, item, header=None, bullet=""):
        """ Given an item recursively iterate over it and print it's leaf nodes
        """
        if header:
            self.print_header(text=header)
            
        if isinstance(item, dict_type): # Dictionary 
            keys = item.keys()
            keys.sort()
            if not bullet: bullet += "  - "
                            
            for k in keys:
                v = item[k]
                if isinstance(v, dict_type) or isinstance(v, collection_type):
                    print bullet + repr(k) + ": "
                    self.print_item(v, bullet="\t"+bullet)
                    
                elif isinstance(k, str) and k.find("time") != -1 and isinstance(v, (int, float)):
                    print bullet + repr(k) + ": " + time.ctime(v)
                
                else:
                    try:
                        print bullet + repr(k) + ": " + str(v)
                    except UnicodeEncodeError:
                        print bullet + repr(k) + ": " + v.encode('ascii', 'replace')
                    
        elif isinstance(item, collection_type): # List, tuple or set 
            if not isinstance(item, list):
                list_item = list(item)
            else:
                list_item = item
            list_item.sort()
            for i in item:
                if isinstance(i, dict_type) or isinstance(i, collection_type):
                    self.print_item(i, bullet="\t-"+bullet)
                    
                else:
                    self.print_item(i, bullet = bullet)
                    
        elif isinstance(item, types.FunctionType): # Function
            self.print_item(item.__name__, bullet=bullet)
            
        else: # Other type
            print bullet, item
            

    def print_header(self, text=None, fill="-"):
        lspace =  "  "
        if not text:
            print lspace + fill * (self.config["header_len"] - len(lspace))
            return

        left = lspace + fill*10
        text = " " + text.strip() + " "
        right = fill * (self.config["header_len"] - (len(left) + len(text)))
        print left + text + right


    def print_info(self, item, opts):
        """ Print function for the command show 
        """
        if not item:
            return
            
        if isinstance(item, collection_type):
            for i in item:
                self.print_info(i, opts)
            return
        
        if isinstance(item, str) and self.oxide.exists("collections_meta", item, {}): # print collection
            cm = self.oxide.retrieve("collections_meta", str(item), {})
            if "verbose" in opts:
                oids = self.oxide.get_field("collections", str(item) , "oid_list")
                files = [ oid + " : " + ", ".join(self.oxide.get_names_from_oid(oid)) 
                           for oid in oids if True ]

                cm["oids"] = files
            self.print_item(cm, header="Collection %s" % item)
            self.print_tags(item)
        
        elif ( isinstance(item, str) and self.oxide.source(item)
            and self.oxide.exists(self.oxide.source(item), item, {}) 
            and "meta" in self.oxide.documentation(self.oxide.source(item)) ): # file or other source
                names = self.oxide.get_names_from_oid(item)
                names = " - Names: " + ", ".join(names)
                self.print_item(names, header="Metadata %s" % item)
                meta_mod = self.oxide.documentation(self.oxide.source(item))["meta"]
                size = self.oxide.get_field(meta_mod, item, "size")
                if size:
                    print "  - Size:", size, "bytes"
                self.print_tags(item)
            
        else:
            self.print_item(item, header="Info")
            
        self.print_header()
      
    
    def print_context(self, verbose=False):
        """ Print function for the command: show context 
        """
        self.print_header(text="Context")
        if not self.context:
            print "  <EMPTY>"
        
        for n, c in enumerate(self.context):
            outstr = "  %s:%s" % (n, ",".join(c[1]))
            #print "  %s:%s" % (n, ",".join(c[1])),
            t = self.oxide.get_field("src_type", c[0], "type")
            outstr += " ( %s "%t
            d = self.oxide.documentation(self.oxide.source(c[0]))
            if "meta" in d:
                size = self.oxide.get_field(d["meta"], c[0], "size")
                if size:
                    outstr += " %s bytes )  "%size
                if verbose:
                    outstr += c[0]
            print outstr
        self.print_header()

        
    def print_collections(self, items, opts):
        """ Print funtcion for the command: show collections
        """
        if "verbose" in opts: 
            self.print_item(self.oxide.retrieve_all("collections_meta"), header="Collections")
        else:
            cm = self.oxide.retrieve_all("collections_meta")
            collections = {}
            for c in cm:
                collections[cm[c]["name"]] = cm[c]["num_oids"]
            self.print_item(collections, header="Collections")
        self.print_header()

     
    def print_modules(self, items, opts):
        """ Print function for the commanbd show modules [ <module_name> ]
        """
        show_private = False
        if "verbose" in opts:
            show_private = True
        if items:
            mod_list = self.oxide.modules_list()
            mod_list.sort()
            for item in items:
                if item not in mod_list:
                    raise ShellSyntaxError("Unrecognized Module %s" %item)
                self.print_mod_details(item)
            return

        for type in self.oxide.module_types_list():
            mod_list = self.oxide.modules_list(type, show_private)
            mod_list.sort()
            self.print_header()
            self.print_item(type.capitalize())
            self.print_header()
            for mod in mod_list:
                self.print_mod_details(mod, short=True)
        self.print_header()
        
        
    def print_mod_details(self, name, short=False):
        """ Print function for the command: show modules <module_name>
        """
        doc = self.oxide.documentation(name)
        if not doc:
            raise ShellSyntaxError("Module %s not found."% name)
        
        if short:
            print "    %s - %s"%(name,doc["description"])
            return
        
        self.print_header(text="Module %s" % name)
        if "description" not in doc or "opts_doc" not in doc:
            raise ShellSyntaxError("Module %s documentation malformed."% name)
        
        print "  - ", doc["description"]
        type = self.oxide.get_mod_type(name)
        print "  -   Type: ", type
        opts_doc = doc["opts_doc"]
        if opts_doc:
            print "  -   Options:"
            self.print_item(opts_doc, bullet="\t-")
        self.print_header()
                
                        
    def print_tags(self, oid):
        """ Print function for printing tags
        """
        tags = self.oxide.get_tags(oid)
        if not tags:
            return
        print
        tags_dict = {"tags":tags}
        self.print_item(tags_dict)
    
    
    ### UTILITIES ##############################################################
    def alias(self, new_alias={}):
        aliases = { "q" : self.do_exit,
                    "!" : self.do_bash,
                  }
        for k in new_alias:
            aliases[k] = new_alias[k]
        return aliases 
        
    def colorize(self, val, effect):
        #return val  # Known bug: escape codes for color really messes up readline.
        effectcodes = {    'cyan':{True:'\x1b[36m',False:'\x1b[39m'},
                           'blue':{True:'\x1b[34m',False:'\x1b[39m'},
                           'red':{True:'\x1b[31m',False:'\x1b[39m'},
                           'magenta':{True:'\x1b[35m',False:'\x1b[39m'},
                           'green':{True:'\x1b[32m',False:'\x1b[39m'},
                      #    'underline':{True:'\x1b[4m' ,False:'\x1b[24m'},
                      #    'bold':{True:'\x1b[1m' ,False:'\x1b[22m'},
                      }
        if effect in effectcodes:
            if val.count("\x1b") == 2: # Strip of existing effects
                val = val.split("\x1b")[1]
                val = val[val.find("m")+1:]
            return effectcodes[effect][True] + val + effectcodes[effect][False]
        return val
        
    def time_filter(self, oid_list, opts):
        """ Given an oid_list and opts with year, mon, day return a filtered 
            oid list where the tags match all of the opts given 
        """
        if "y" in opts:
            opts["year"] = opts["y"]
        if "m" in opts:
            opts["month"] = opts["m"]
        if "mon" in opts:
            opts["month"] = opts["mon"]
        if "d" in opts:
            opts["day"] = opts["d"]
            
        if not "year" in opts and not "month" in opts and not "day" in opts:
            return oid_list

        if "year" in opts and opts["year"] < 100:
            now = time.localtime(time.time())
            if now.tm_year >= opts["year"]+2000:
                opts["year"] += 2000
            else:
                opts["year"] += 1900
            
        year, mon, day = None, None, None
        if "year" in opts:
            year = opts["year"]
        if "month" in opts:
            mon = opts["month"]
        if "day" in opts:
            day = opts["day"]
            
        filtered_oids = []
        for oid in oid_list:
            tags = self.oxide.get_tags(oid)
            for tag in tags:
                if "time" in tag and isinstance(tags[tag], (float, int)):
                    t = time.localtime(tags[tag])
                    if (year and mon and day and year == t.tm_year 
                       and mon == t.tm_mon and day == t.tm_mday):
                            filtered_oids.append(oid)
                    elif year and mon and year == t.tm_year and mon == t.tm_mon:
                            filtered_oids.append(oid)
                    elif mon and day and mon == t.tm_mon and day == t.tm_mday:
                            filtered_oids.append(oid)
                    elif year and day and year == t.tm_year and day == t.tm_mday:
                            filtered_oids.append(oid)
                    elif year and year == t.tm_year:
                        filtered_oids.append(oid)
                    elif mon and mon == t.tm_mon:
                        filtered_oids.append(oid)
                    elif day and day == t.tm_mday:
                        filtered_oids.append(oid)
        return filtered_oids
        
        
    def tag_value_split(self, arg):
        """ given 
        """
        tv = arg.split(":")
        if len(tv) == 1:
            return arg, "<empty>"
        else:
            tag = tv[0]
            value = tv[1]
            return tag, value
      
      
    def get_plugin_function(self, fname):
        if fname not in self.plugin_function_names():
            return None
        for p in self.plugins:
            for f in self.plugins[p]:
                if fname == f.__name__:
                    return f
        
    def plugin_function_names(self):
        func_names = []
        for p in self.plugins:
            for f in self.plugins[p]:
                func_names.append(f.__name__)
        return func_names

    
    ### TAB COMPLETION #########################################################
    def complete_bash(self, text, line, begidx, endidx):
        return glob(text+"*")

    def complete_collection(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        control = line[begidx-1]
        if (len(line.split()) > 1 and len(line.split(" ")) < 4 and
               line.split()[1] in ("delete","rename","add","remove")):
            return self.completions(text, self.oxide.collection_names(), control)
        return self.completions(text, self.commands["collection"], control)
        
    def complete_context(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        control = line[begidx-1]
        if line.find("load") != -1:
            return glob(text+"*")
        return self.completions(text, self.commands["context"], control)
        
    def complete_help(self, text, line, begidx, endidx):
        control = line[begidx-1]
        topics = self.commands.keys()
        topics.extend(self.plugin_function_names())
        return self.completions(text, topics, control)
                
    def complete_history(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        control = line[begidx-1]
        return self.completions(text, self.commands["history"], control)
        
    def complete_import(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        return glob(text+"*")

    def complete_load(self, text, line, begidx, endidx):
        return glob(text+"*.txt")
                
    def complete_plugin(self, text, line, begidx, endidx):
        files = glob(os.path.join("plugins", "*.py"))
        files = [ os.path.split(file)[1].replace(".py", "")
                   for file in files if not "__init__" in file ]
        return self.completions(text, files, "")
        
    def complete_run(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        length = len(line.split())
        if length <= 2 and not (length == 2 and not text):
            return self.mod_completions(text, False)
        control = line[begidx-1]
        return self.completions(text, [], control)
    
    def complete_show(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        if line.count("modules") > 0:
            return self.mod_completions(text)
        control = line[begidx-1]
        if control == "-":
            return self.complete_options(text, line, commands, control) 
        return self.completions(text, self.show_completions, control)

    def complete_drop(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        control = line[begidx-1]
        return self.completions(text, self.commands["drop"], control)

    def complete_tag(self, text, line, begidx, endidx):
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)
        control = line[begidx-1]
        return self.completions(text, self.commands["tag"], control)
        
    #### TAB UTILITIES #########################################################
    def completedefault(self, *ignored):
        """Method called to complete an input line when no command-specific
        complete_*() method is available.

        By default, it returns an empty list.

        """
        text = ignored[0]
        line = ignored[1]
        begidx = ignored[2]
        endidx = ignored[3]
        control = line[begidx-1]
        if "|" in line:
            return self.pipe_complete(text, line, begidx, endidx)

        commands = None
        split = line.split(" ")
        if len(split) < 2:
            commands = self.commands.keys()
            commands.extend(self.plugin_function_names())
        elif len(split) < 3:
            if split[0] in self.commands:
                commands = self.commands[split[0]]

                for f in commands:
                    if f.startswith(split[1]):
                        break;
                else:
                    commands = None

        if control == "-":
            return self.complete_options(text, line, commands, control)    

        return self.completions(text, commands, control)
    
    def complete_options(self, text, line, commands, control):
        if "--" in line:
            return [ f for f in ["verbose"] if f.startswith(text) ]
        elif "-" in line:
            return [ f for f in ["-verbose"] if f.startswith(text) ]
        return self.completions(text, commands, control)
    
    def completenames(self, text, *ignored): # Overwrite cmd function
        commands = self.commands.keys()
        commands.extend(self.plugin_function_names())
        control = text[len(text)-1:]
        return self.completions(text, commands, control)

    def mod_completions(self, text, verbose=True):
        opts = self.oxide.modules_list()
        return [f for f in opts if f.startswith(text)]

    def pipe_complete(self, text, line, begidx, endidx):
        rline = line.split("|")[line.count("|")].lstrip() # Get everything to the right of the right most pipe
        command = ""
        control = line[begidx-1]

        commands = None
        split = rline.split(" ")
        if len(split) < 2:
            commands = self.commands.keys()
            commands.extend(self.plugin_function_names())
        elif len(split) < 3:
            if split[0] in self.commands:
                commands = self.commands[split[0]]

                for f in commands:
                    if f.startswith(split[1]):
                        break;
                else:
                    commands = None

        if len(rline.split()) > 0:
            command = rline.split()[0]
        if command in self.commands: # Call the orig commplete_ func with necessary mods
            d = len(line)-len(rline)
            begidx = begidx - d # Adjust the begidx
            endidx = endidx - d # Adjust the endidx
            try:
                return getattr(self, "complete_"+command)(text, rline, begidx, endidx)
            except AttributeError:
                return self.completions(text, commands, control) 
        return self.completions(text, commands, control) 

    def completions(self, text, subcommands, control):
        if control == "@":
            return [ f for f in self.vars.keys() if f.startswith(text) ]
        elif control == "&":
            return [ f for f in self.oxide.collection_names() if f.startswith(text) ]
        else:
            if not text:
                return subcommands
            if not subcommands:
                return glob(text+"*")
            else:
                return [ f for f in subcommands if f.startswith(text) ]
