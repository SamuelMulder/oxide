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

import os, logging, ConfigParser, sys_utils
from otypes import cast_string 
from otypes import convert_logging_level

name = "config"

dir_root = sys_utils.root_dir
dir_oxide = sys_utils.oxide_dir

config_file = ".config.txt"
config_file_fp = os.path.join(dir_root, config_file)

# Global config defaults will be used when a new config is created or if a section is missing
# Global vars are section_option
dir_defaults = {"root"          :dir_root, 
                "oxide"         :dir_oxide,
                "libraries"     :os.path.join(dir_oxide, "libraries"),
                "modules"       :os.path.join(dir_root, "modules"),
                "datasets"      :os.path.join(dir_root, "datasets"),
                "datastore"     :os.path.join(dir_root, "db"),
                "localstore"    :os.path.join(dir_root, "localstore"),
                "logs"          :dir_root,
                "reference"     :os.path.join(dir_oxide, "reference"),
                "scratch"       :os.path.join(dir_root, "scratch"),
                "sample_dataset":os.path.join(dir_root, "datasets", "sample_dataset"),
                }


logging_defaults = {"level":"INFO",
                    "rotate":"False",
                    "max_log_size":"10",
                    "num_log_files":"5"}

verbosity_defaults = {"level":"WARN"}

multiproc_defaults = {"on":"False",
                      "max":"3"}

file_defaults = {"max":"1024",
                 "process_unrecognized_formats":"false"}

distributed_defaults = {"port":"8000",
                        "compute_nodes":"localhost"}

dev_mode = {"enable": "True"}

django = {"ip":"0.0.0.0",
          "port":"8888"}
          
plugins = {"default":"True"}

history = {"file":".history.txt",
           "max": 200}

all_defaults = {"dir"        :dir_defaults,
                "logging"    :logging_defaults, 
                "verbosity"  :verbosity_defaults, 
                "multiproc"  :multiproc_defaults,
                "file"       :file_defaults,
                "distributed":distributed_defaults,
                "dev_mode"   :dev_mode,
                "django"     :django,
                "plugins"    :plugins,
                "history"    :history,
               }
                      
rcp = ConfigParser.RawConfigParser()
config_changed = False
setup_run = False

def config_menu(section="all"):
    if section == "all":
        sections = rcp.sections()
    elif section not in rcp.sections():
        print " - Section %s not found"
        return False
    else:
        sections = [section]

    r = raw_input(" - Set all to defaults (Y/n): ").strip().lower()
    if r != 'n':
       set_config_all_to_defaults()
       return True 
    print " - <Enter> to leave value unchanged "
    print " - d to use default value"
    print " - q to abort all changes"
    print " - c to leave the rest unchanged"
    print
    print " [section]"
    print " <option> = <cur_val>    <default>"
    print 
    for section in sections:
        print " [%s]" % (section)
        for option in all_defaults[section]:
            cval = rcp.get(section, option)
            dval = all_defaults[section][option]
            if str(cval).lower() != str(dval).lower():
                print "   %s = %s    <%s>" % (option, cval, dval)
            else:
                print "   %s = %s" % (option, cval)
            nval = raw_input("   > ").strip()
            if nval == "":
                continue
            elif nval.lower() == 'c':
                return True
            elif nval.lower() == 'd':
                set_value(section, option, dval)
            elif nval.lower() == 'q':
                return False
            else:
                set_value(section, option, nval)
    return True

def setup(section="all", initial_setup=False):
    """ Set up or change config
    """
    global setup_run
    if setup_run:
      return
    elif initial_setup:
        print " - Initial setup"
        set_config_all_to_defaults()
    else:
        r = raw_input(" - Change config (Y/n): ").strip().lower()
        if r == 'n':
          return

    if not config_menu(section):
        print " - Aborting all changes to config"
        exit()
    r = raw_input(" - Write changes to config file (Y/n): ").strip().lower()
    if r != 'n':
        print " - Writing changes to config file", config_file 
        write_config_file()
    else:
        print " - Aborting all changes to config"
        exit()

    setup_run = True

def init():

    # Check if the config file exists. If not create it using defaults
    if not os.path.isfile(config_file_fp):
        setup(section="all", initial_setup=True)
        
    read_config_file()
    set_globals()
    sanity_check()
    
    if config_changed:
        set_globals()
        write_config_file()

def sanity_check():
    validate_dir_root()
    validate_dir_oxide()

def validate_dir_root():
    logging.debug("Asserting that root dir in the config is valid for this environment.")
    global dir_root
    global config_changed
    if os.path.realpath(dir_root) != os.path.realpath(sys_utils.root_dir):
        logging.warning("root dir in config invalid for this environment, resetting")
        dir_root = sys_utils.root_dir
        set_value("dir", "root", dir_root)
        config_changed = True
        
def validate_dir_oxide():
    logging.debug("Asserting that root dir in the config is valid for this environment.")
    global dir_oxide
    global config_changed
    if os.path.realpath(dir_oxide) != os.path.realpath(sys_utils.oxide_dir):
       logging.warning("oxide dir in config invalid for this environment, resetting")
       dir_oxide = sys_utils.oxide_dir
       set_value("dir", "oxide", dir_oxide)
       config_changed = True

def write_config_file():
    try:
        logging.info("Writing config to %s", config_file_fp)
        fd = file(config_file_fp, "w")
        rcp.write(fd)
        fd.close()
    except IOError, err:
        logging.error("%s", err)
        logging.error("Unable to write config file %s", config_file_fp)

def read_config(fd):
    """ Reads the configuration in the file referenced by fd.
        the global config_file string variable is only used in error handling
    """
    try:
        rcp.readfp(fd, config_file_fp)
    except IOError, e:
        logging.error("ConfigParse exception:%s", e)

def read_config_file():
    """ This function opens a file based on
        the global config_file string and calls
        read_config to actually read the configuration in
    """
    try:
        logging.debug("Reading config file %s", config_file_fp)
        fd = file(config_file_fp, "r")
        read_config(fd)
        fd.close()
        return True
    except:
        logging.error("Unable to read config file %s", config_file_fp)
        return False
            
def set_config_all_to_defaults():
    """ Iterate over the defaults and set the according values
    """
    logging.debug("Creating default config")
    for section in all_defaults:
        set_config_section_to_defaults(section)
    global config_changed
    config_changed = True

def set_config_section_to_defaults(section):
    if not rcp.has_section(section):
        rcp.add_section(section)
    for option in all_defaults[section]:
        set_config_option_to_default(section, option)
    global config_changed
    config_changed = True
        
def set_config_option_to_default(section, option):
    rcp.set(section, option, all_defaults[section][option])
    global config_changed
    config_changed = True
        
def set_global_option(section, option, value):
    var = section + "_" + option
    value = cast_string(value)
    globals()[var] = value

def get_value_or_set_to_default(section, option):
    try:
        value = rcp.get(section, option)
        if value == "":
            logging.warn(" Empty config option %s in section %s - setting to default", option, section)
            set_config_option_to_default(section, option)
    except ConfigParser.NoOptionError:
        logging.warn(" Missing or new config option %s in section %s - setting to default", option, section)
        set_config_option_to_default(section, option)
        value = rcp.get(section, option)
    return value

def set_globals():
    """ If possible, use values from config file otherwise use defaults
        global variables are section_option
    """
    logging.debug("Setting globals in config")
    for section in all_defaults:
        if not rcp.has_section(section):
            set_config_section_to_defaults(section)
            global config_changed
            config_changed = True
        for option in all_defaults[section]:
            value = get_value_or_set_to_default(section, option)                
            set_global_option(section, option, value)
    return True

def set_value(section, option, value):
    """ This function sets an option in the config 
		file but leaves the other values the same.
    """
    if not rcp.has_section( section ):
        rcp.add_section( section )
    rcp.set(section, option, value)
    global config_changed
    config_changed = True
    
def write_config_file(new_config_file=None):
    """ This function opens a file based on
        the global config_file string and writes the
        current configuration out to it.
    """
    global config_file
    if new_config_file:
        config_file = new_config_file
    try:
        logging.debug("Writing config to %s", config_file_fp)
        fd = file(config_file_fp, "w")
        rcp.write(fd)
        fd.close()
        
    except IOError, err:
        logging.error("Unable to write config file %s", config_file_fp)
        logging.error(str(err)) 
    
def get_logging_level():
    """ Return the logging level from the config
    """
    try:
        level = rcp.get("logging","level").upper()
        return convert_logging_level(level)
    except:
        logging.warning("[logging] section of the config malformed.")
        return False
        
def get_verbosity_level():
    """ Return the verbostiy level from the config
    """
    try:
        level = rcp.get("verbosity","level").upper()
        return convert_logging_level(level)
    except:
        logging.warning("[verbosity] section of the config malformed.")
        return False

def get_section(section):
    sdict = {}
    for option in rcp.options(section):
        sdict[option] = rcp.get(section,option)
    return sdict

def get_all():
    """ Return a dictionary of dictionaries with the sections, options and values
    """  
    cdict = {}
    for section in rcp.sections():
        cdict[section] = get_section(section)
    return cdict
    
def get_value(section, option):
    """ Given a section and an option return the value 
    """
    try:
        value = rcp.get(section, option)
        return value
    except:
        logging.error("Tried to retrieve nonexistant value from config (%s:%s).",
                      section, option)
        return False

def create_shortcuts():
    """ Creates desktop shortcuts for Oxide 
    """
    desktop_path = os.path.expanduser("~") + "/Desktop/"
    oxide_path = os.getcwd()

    launch_oxide = "[Desktop Entry]\nVersion=1.0\nName=Launch Oxide\nComment=Launch Oxide Shell\n\
                    Exec=-e %s/oxide\nIcon=%s/docs/logos/Oxide_Logo.png\n\
                    Terminal=true\nType=Application\nCategories=Utility;\nStartupNotify=true" % (oxide_path, oxide_path)

    launch_oxide_root = "[Desktop Entry]\nVersion=1.0\nName=Launch Oxide as Root\nComment=Launch Oxide Shell as Root\n\
                    Exec=-e %s/oxide -r\nIcon=%s/docs/logos/Oxide_Root_Logo.png\n\
                    Terminal=true\nType=Application\nCategories=Utility;\nStartupNotify=true" % (oxide_path, oxide_path)

    launch_oxide_update = "[Desktop Entry]\nVersion=1.0\nName=Update Oxide\nComment=Launch Oxide Updater\n\
                    Exec=-e %s/utils/update.sh -r\nIcon=%s/docs/logos/Oxide_Update_Logo.png\n\
                    Terminal=true\nType=Application\nCategories=Utility;\nStartupNotify=true" % (oxide_path, oxide_path)

    with open(desktop_path + 'oxide3.desktop', 'w') as f:
        f.write(launch_oxide_update)

    with open(desktop_path + 'oxide2.desktop', 'w') as f:
        f.write(launch_oxide_root)

    with open(desktop_path + 'oxide1.desktop', 'w') as f:
        f.write(launch_oxide)
        
init()        
