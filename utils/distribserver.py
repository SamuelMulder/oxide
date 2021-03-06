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

import core.distribution_server as oxide_server
import optparse, sys
parser = optparse.OptionParser()
parser.add_option("-l", "--listen", action="store", type=str, dest="listen",
                    help="The ip:port I'm listening on")
(options, args) = parser.parse_args()


if __name__ == "__main__":
    if not isinstance(options.listen, str): 
        parser.print_help()
        exit(1)

    elif len(options.listen.split(":")) != 2:
        parser.print_help()
        exit(1)

    my_ip = str(options.listen.split(":")[0])
    my_port = int(options.listen.split(":")[1])
    sys.argv = sys.argv[:1]
    oxide_server.main(my_ip, my_port)
