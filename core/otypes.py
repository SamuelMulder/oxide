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

import logging

log_levels = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]
class OxideError(Exception):
    pass    

class BadOIDList(OxideError):
    pass
    
class UnrecognizedModule(OxideError):
    pass
    
class AnalysisModuleError(OxideError):
    pass

class InvalidOIDList(AnalysisModuleError):
    pass

def cast_string(s):
    if not isinstance (s, str) or s == "":
        return s
    elif s.lower() == "true":
        return True
    elif s.lower() == "false":
        return False        
    elif s.upper() in log_levels:
        return convert_logging_level(s)
    try:
        return int(s)
    except:
        try:
            return float(s)
        except:
            logging.debug("Not able to cast(%s)", s)
            return s
            
def convert_logging_level(level):
    """ Given a string corresponding to a loggging level return a logging
		level or False if a match is not found
    """
    level = level.upper()
    if level == "DEBUG":
        return logging.DEBUG
    elif level == "INFO":
        return logging.INFO
    elif level == "WARN" or level ==  "WARNING":
        return logging.WARN
    elif level == "ERROR":
        return logging.ERROR
    elif level == "CRITICAL" or level == "FATAL":
        return logging.CRITICAL
    else:
        return False	
