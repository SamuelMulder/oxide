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

import api
import pdf_parser

def dump_js(args, opts):
    valid, invalid = api.valid_oids(args)
    oids = api.expand_oids(valid)
    
    if not oids:
        raise ShellSyntaxError("No valid oids")
    
    for o in oids:
        type = api.get_field("src_type", o, "type")
        if type != "PDF":
            continue
        src = api.source(o)
        data = api.get_field(src, o, "data")
        i = data.find("<script")
        while i > -1:
            j = data.find("</script>")
            if j > -1:
                print "Found script:"
                print data[i:j+9]
            data = data[j:]
            i = data.find("<script")

exports = [dump_js]
